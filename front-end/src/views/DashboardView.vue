<script setup>
import { ref, computed, onMounted } from 'vue'
import { RouterLink } from 'vue-router'
import DefaultLayout from '../layouts/DefaultLayout.vue'
import { useAuthStore } from '../stores/auth'

const api = 'http://localhost:8000'
const authStore = useAuthStore()

// Alunos que ainda estão vinculados ao programa (entram no risco de desligamento).
const statusEmCurso = ['ATIVO', 'TRANCADO', 'PROCESSO DE DESLIGAMENTO']
const conceitosAprovados = ['APROVADO', 'APROVADO_CONDICIONALMENTE']
const limiteLinhas = 5
const diasRiscoAlto = 30
const diasRiscoMedio = 60
const diasVersaoFinalUrgente = 7

const estudantes = ref([])
const qualificacoes = ref([])
const defesas = ref([])
const dissertacoes = ref([])
const professores = ref([])
const carregando = ref(true)
const erro = ref('')

const verTodosRisco = ref(false)
const verTodasVersoes = ref(false)

// ---------- Datas ----------

function inicioDoDia(data) {
  return new Date(data.getFullYear(), data.getMonth(), data.getDate())
}

const hoje = inicioDoDia(new Date())

// "2026-11-10" vira uma data local (new Date("2026-11-10") seria lido em UTC).
function lerData(texto) {
  if (!texto) return null
  const [ano, mes, dia] = texto.slice(0, 10).split('-').map(Number)
  if (!ano || !mes || !dia) return null
  return new Date(ano, mes - 1, dia)
}

function formatarData(texto) {
  const data = lerData(texto)
  if (!data) return '—'
  const dia = String(data.getDate()).padStart(2, '0')
  const mes = String(data.getMonth() + 1).padStart(2, '0')
  return `${dia}/${mes}/${data.getFullYear()}`
}

// Quantos dias faltam (negativo = já passou).
function diasAte(texto) {
  const data = lerData(texto)
  if (!data) return null
  return Math.round((data - hoje) / (1000 * 60 * 60 * 24))
}

function noMesAtual(texto) {
  const data = lerData(texto)
  return (
    data !== null &&
    data.getMonth() === hoje.getMonth() &&
    data.getFullYear() === hoje.getFullYear()
  )
}

// Deste mês e de hoje em diante (o que ainda vai acontecer).
function aindaNesteMes(texto) {
  const dias = diasAte(texto)
  return noMesAtual(texto) && dias !== null && dias >= 0
}

function antesDeHoje(texto) {
  const dias = diasAte(texto)
  return dias !== null && dias < 0
}

function textoDias(dias) {
  if (dias === 0) return 'hoje'
  if (dias === 1) return 'amanhã'
  if (dias < 0) return `vencido há ${Math.abs(dias)} dia${dias === -1 ? '' : 's'}`
  return `em ${dias} dias`
}

// ---------- Busca dos dados ----------

function cabecalho() {
  return { Authorization: `Bearer ${authStore.token}` }
}

async function buscarJson(caminho) {
  const resposta = await fetch(`${api}${caminho}`, { headers: cabecalho() })
  if (resposta.status === 401) throw new Error('sessao')
  if (resposta.status === 404) return []
  if (!resposta.ok) throw new Error(`${caminho} ${resposta.status}`)
  return resposta.json()
}

// A rota de estudantes devolve no máximo 200 por vez: pedimos de 200 em 200.
async function buscarTodosEstudantes() {
  const todos = []
  let skip = 0
  let total = Infinity
  while (skip < total) {
    const pagina = await buscarJson(`/estudantes?skip=${skip}&limit=200`)
    const itens = pagina.itens || []
    todos.push(...itens)
    total = pagina.total ?? todos.length
    if (itens.length === 0) break
    skip += itens.length
  }
  return todos
}

function paraLista(dados) {
  if (Array.isArray(dados)) return dados
  return dados ? [dados] : []
}

async function carregarPainel() {
  carregando.value = true
  erro.value = ''
  try {
    const [listaEstudantes, listaQualificacoes, listaDefesas, listaDissertacoes, listaProfessores] =
      await Promise.all([
        buscarTodosEstudantes(),
        buscarJson('/qualificacoes'),
        buscarJson('/defesas'),
        buscarJson('/dissertacoes'),
        buscarJson('/professores?limit=200'),
      ])
    estudantes.value = listaEstudantes
    qualificacoes.value = paraLista(listaQualificacoes)
    defesas.value = paraLista(listaDefesas)
    dissertacoes.value = paraLista(listaDissertacoes)
    professores.value = paraLista(listaProfessores)
  } catch (e) {
    erro.value =
      e.message === 'sessao'
        ? 'Sua sessão expirou. Saia e entre de novo.'
        : 'Não foi possível carregar o painel. Tente de novo em instantes.'
  } finally {
    carregando.value = false
  }
}

// ---------- Mapas (consulta rápida por id) ----------

const estudantePorId = computed(() => new Map(estudantes.value.map((e) => [e.id_estudante, e])))
const professorPorId = computed(() => new Map(professores.value.map((p) => [p.id_professor, p])))
const estudanteDaDissertacao = computed(
  () => new Map(dissertacoes.value.map((d) => [d.id_dissertacao, d.id_estudante])),
)

function nomeOrientador(estudante) {
  if (!estudante?.id_orientador) return '—'
  return professorPorId.value.get(estudante.id_orientador)?.nome_professor || '—'
}

// ---------- US1: cards ----------

const totalAtivos = computed(
  () => estudantes.value.filter((e) => e.status_atual === 'ATIVO').length,
)

// Bancas que ainda vão acontecer neste mês. As que já passaram sem resultado
// aparecem em "Atas pendentes" (assim a mesma banca não conta duas vezes).
const bancasDoMes = computed(() => {
  const qualificacoesDoMes = qualificacoes.value.filter(
    (q) => aindaNesteMes(q.data_realizacao) && q.status_qualificacao === 'PENDENTE',
  )
  const defesasDoMes = defesas.value.filter(
    (d) => aindaNesteMes(d.data_realizacao) && d.status_defesa === 'PENDENTE',
  )
  return qualificacoesDoMes.length + defesasDoMes.length
})

// Qualificação: a banca já aconteceu, mas o resultado ainda não foi registrado.
// Usamos o status (e não o "retorno"), porque o retorno fica vazio até em
// qualificações já resolvidas, e ele vai ser trocado por "resultado" na task do João.
function qualificacaoSemAta(qualificacao) {
  return (
    antesDeHoje(qualificacao.data_realizacao) && qualificacao.status_qualificacao === 'PENDENTE'
  )
}

// Defesa: a banca já aconteceu, mas o conceito ainda não foi registrado.
function defesaSemAta(defesa) {
  return antesDeHoje(defesa.data_realizacao) && !defesa.conceito_defesa
}

const atasPendentes = computed(
  () =>
    qualificacoes.value.filter(qualificacaoSemAta).length +
    defesas.value.filter(defesaSemAta).length,
)

// ---------- US2: tabelas ----------

// Prazo do SIGAA vencendo nos próximos 60 dias (mais urgente primeiro).
const riscoDesligamento = computed(() =>
  estudantes.value
    .filter((e) => statusEmCurso.includes(e.status_atual))
    .map((e) => ({ estudante: e, dias: diasAte(e.prazo_conclusao_sigaa) }))
    .filter((item) => item.dias !== null && item.dias >= 0 && item.dias <= diasRiscoMedio)
    .sort((a, b) => a.dias - b.dias),
)

// Defesas aprovadas aguardando a versão final (prazo mais próximo primeiro).
const versoesPendentes = computed(() =>
  defesas.value
    .filter(
      (d) =>
        d.status_defesa === 'AGUARDANDO_VERSAO_FINAL' &&
        conceitosAprovados.includes(d.conceito_defesa),
    )
    .map((d) => {
      const idEstudante = estudanteDaDissertacao.value.get(d.id_dissertacao) ?? null
      return {
        defesa: d,
        idEstudante,
        estudante: estudantePorId.value.get(idEstudante) || null,
        dias: diasAte(d.prazo_versao_final),
      }
    })
    .sort((a, b) => (a.dias ?? Infinity) - (b.dias ?? Infinity)),
)

const riscoVisivel = computed(() =>
  verTodosRisco.value ? riscoDesligamento.value : riscoDesligamento.value.slice(0, limiteLinhas),
)
const versoesVisiveis = computed(() =>
  verTodasVersoes.value ? versoesPendentes.value : versoesPendentes.value.slice(0, limiteLinhas),
)

// Alunos diferentes nas duas listas (o Set não deixa contar o mesmo aluno duas vezes).
const prazosCriticos = computed(() => {
  const ids = new Set()
  riscoDesligamento.value.forEach((item) => ids.add(item.estudante.id_estudante))
  versoesPendentes.value.forEach((item) => {
    if (item.idEstudante !== null) ids.add(item.idEstudante)
  })
  return ids.size
})

const cards = computed(() => [
  { titulo: 'Alunos ativos', valor: totalAtivos.value, critico: false },
  { titulo: 'Bancas agendadas (mês)', valor: bancasDoMes.value, critico: false },
  { titulo: 'Atas pendentes', valor: atasPendentes.value, critico: false },
  { titulo: 'Prazos críticos', valor: prazosCriticos.value, critico: true },
])

function classeRisco(dias) {
  return dias <= diasRiscoAlto ? 'bg-rose-100 text-rose-700' : 'bg-amber-100 text-amber-800'
}

function versaoUrgente(dias) {
  return dias !== null && dias < diasVersaoFinalUrgente
}

onMounted(carregarPainel)
</script>

<template>
  <DefaultLayout>
    <div class="mb-8 bg-white p-6 rounded-2xl border border-gray-200 shadow-sm">
      <h2 class="text-2xl font-bold text-gray-900">Painel Principal</h2>
      <p class="text-sm text-gray-500 mt-1">Resumo do programa e alunos que precisam de atenção.</p>
    </div>

    <p
      v-if="erro"
      class="mb-8 px-4 py-3 rounded-xl border border-rose-200 bg-rose-50 text-rose-700 text-sm"
    >
      {{ erro }}
    </p>

    <!-- US1: cards de resumo -->
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
      <div
        v-for="card in cards"
        :key="card.titulo"
        class="p-5 rounded-xl border shadow-sm"
        :class="card.critico ? 'bg-rose-50 border-rose-200' : 'bg-white border-gray-200'"
      >
        <p
          class="text-xs font-semibold uppercase tracking-wider mb-1"
          :class="card.critico ? 'text-rose-700' : 'text-gray-500'"
        >
          {{ card.titulo }}
        </p>
        <p
          class="text-3xl font-extrabold"
          :class="card.critico ? 'text-rose-600' : 'text-gray-900'"
        >
          {{ carregando || erro ? '—' : card.valor }}
        </p>
      </div>
    </div>

    <!-- US2: risco de desligamento -->
    <section class="mb-8 bg-white rounded-2xl border border-gray-200 shadow-sm">
      <div class="px-6 pt-6 pb-4 flex flex-wrap items-center justify-between gap-3">
        <div>
          <h3 class="text-lg font-bold text-gray-900">Risco de desligamento</h3>
          <p class="text-sm text-gray-500">Prazo do SIGAA vencendo nos próximos 60 dias.</p>
        </div>
        <button
          v-if="riscoDesligamento.length > limiteLinhas"
          type="button"
          class="text-sm font-medium text-blue-700 hover:underline"
          @click="verTodosRisco = !verTodosRisco"
        >
          {{ verTodosRisco ? 'Mostrar menos' : `Ver todos (${riscoDesligamento.length})` }}
        </button>
      </div>

      <p v-if="carregando" class="px-6 pb-6 text-sm italic text-gray-500">Carregando...</p>
      <p v-else-if="erro" class="px-6 pb-6 text-sm italic text-gray-500">—</p>
      <p v-else-if="riscoDesligamento.length === 0" class="px-6 pb-6 text-sm italic text-gray-500">
        Nenhum aluno com prazo do SIGAA nos próximos 60 dias.
      </p>
      <div v-else class="overflow-x-auto">
        <table class="w-full text-sm">
          <thead class="bg-gray-50 text-left text-gray-700">
            <tr>
              <th class="px-6 py-3 font-semibold">Aluno</th>
              <th class="px-6 py-3 font-semibold">Orientador</th>
              <th class="px-6 py-3 font-semibold">Data limite</th>
              <th class="px-6 py-3 font-semibold">Motivo</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="item in riscoVisivel"
              :key="item.estudante.id_estudante"
              class="border-t border-gray-200"
            >
              <td class="px-6 py-3">
                <RouterLink
                  :to="`/estudantes/${item.estudante.id_estudante}`"
                  class="font-medium text-blue-700 hover:underline"
                >
                  {{ item.estudante.nome_discente }}
                </RouterLink>
              </td>
              <td class="px-6 py-3 text-gray-600">{{ nomeOrientador(item.estudante) }}</td>
              <td class="px-6 py-3 text-gray-600 whitespace-nowrap">
                {{ formatarData(item.estudante.prazo_conclusao_sigaa) }}
              </td>
              <td class="px-6 py-3">
                <span
                  class="inline-block px-2.5 py-1 rounded-full text-xs font-semibold whitespace-nowrap"
                  :class="classeRisco(item.dias)"
                >
                  Vencimento SIGAA {{ textoDias(item.dias) }}
                </span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <!-- US2: versões finais pendentes -->
    <section class="mb-8 bg-white rounded-2xl border border-gray-200 shadow-sm">
      <div class="px-6 pt-6 pb-4 flex flex-wrap items-center justify-between gap-3">
        <div>
          <h3 class="text-lg font-bold text-gray-900">Versões finais pendentes</h3>
          <p class="text-sm text-gray-500">
            Defesas aprovadas aguardando a entrega da versão final.
          </p>
        </div>
        <button
          v-if="versoesPendentes.length > limiteLinhas"
          type="button"
          class="text-sm font-medium text-blue-700 hover:underline"
          @click="verTodasVersoes = !verTodasVersoes"
        >
          {{ verTodasVersoes ? 'Mostrar menos' : `Ver todos (${versoesPendentes.length})` }}
        </button>
      </div>

      <p v-if="carregando" class="px-6 pb-6 text-sm italic text-gray-500">Carregando...</p>
      <p v-else-if="erro" class="px-6 pb-6 text-sm italic text-gray-500">—</p>
      <p v-else-if="versoesPendentes.length === 0" class="px-6 pb-6 text-sm italic text-gray-500">
        Nenhuma versão final pendente.
      </p>
      <div v-else class="overflow-x-auto">
        <table class="w-full text-sm">
          <thead class="bg-gray-50 text-left text-gray-700">
            <tr>
              <th class="px-6 py-3 font-semibold">Aluno</th>
              <th class="px-6 py-3 font-semibold">Orientador</th>
              <th class="px-6 py-3 font-semibold">Prazo da versão final</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="item in versoesVisiveis"
              :key="item.defesa.id_defesa"
              class="border-t border-gray-200"
            >
              <td class="px-6 py-3">
                <RouterLink
                  v-if="item.estudante"
                  :to="`/estudantes/${item.estudante.id_estudante}`"
                  class="font-medium text-blue-700 hover:underline"
                >
                  {{ item.estudante.nome_discente }}
                </RouterLink>
                <span v-else class="text-gray-500">Aluno não encontrado</span>
              </td>
              <td class="px-6 py-3 text-gray-600">{{ nomeOrientador(item.estudante) }}</td>
              <td class="px-6 py-3 whitespace-nowrap">
                <span
                  :class="
                    versaoUrgente(item.dias) ? 'font-semibold text-rose-600' : 'text-gray-600'
                  "
                >
                  {{ formatarData(item.defesa.prazo_versao_final) }}
                </span>
                <span
                  v-if="item.dias !== null"
                  class="ml-2 text-xs"
                  :class="versaoUrgente(item.dias) ? 'text-rose-600' : 'text-gray-500'"
                >
                  ({{ textoDias(item.dias) }})
                </span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>
  </DefaultLayout>
</template>
