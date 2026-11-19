<script setup>
import { ref, computed, onMounted } from 'vue'
import DefaultLayout from '../layouts/DefaultLayout.vue'
import {
  buscarAlertasPendentes,
  buscarHistoricoAlertas,
  usandoDadosDeExemplo,
} from '../services/alertas'

// Níveis de urgência, como na task:
// crítico = vencido ou até 7 dias; atenção = 8 a 30; preventivo = mais de 30.
const niveis = [
  {
    chave: 'critico',
    rotulo: 'Crítico',
    descricao: 'Vencidos ou até 7 dias',
    classeCard: 'bg-rose-50 border-rose-200',
    classeTitulo: 'text-rose-700',
    classeValor: 'text-rose-600',
    classeAba: 'border-rose-500 text-rose-700',
    classeSelo: 'bg-rose-100 text-rose-700',
  },
  {
    chave: 'atencao',
    rotulo: 'Atenção',
    descricao: 'De 8 a 30 dias',
    classeCard: 'bg-amber-50 border-amber-200',
    classeTitulo: 'text-amber-800',
    classeValor: 'text-amber-600',
    classeAba: 'border-amber-500 text-amber-800',
    classeSelo: 'bg-amber-100 text-amber-800',
  },
  {
    chave: 'preventivo',
    rotulo: 'Preventivo',
    descricao: 'Mais de 30 dias',
    classeCard: 'bg-blue-50 border-blue-200',
    classeTitulo: 'text-blue-800',
    classeValor: 'text-blue-600',
    classeAba: 'border-blue-500 text-blue-800',
    classeSelo: 'bg-blue-100 text-blue-800',
  },
]

const pendentes = ref([])
const historico = ref([])
const carregando = ref(true)
const erro = ref('')
const abaAtiva = ref('critico')

// Filtros rápidos
const busca = ref('')
const filtroTipo = ref('')
const filtroBolsista = ref('')

// ---------- Funções de apoio ----------

function nivelUrgencia(dias) {
  if (dias <= 7) return 'critico'
  if (dias <= 30) return 'atencao'
  return 'preventivo'
}

function classeSeloDias(dias) {
  return niveis.find((n) => n.chave === nivelUrgencia(dias)).classeSelo
}

function normalizar(texto) {
  return String(texto ?? '')
    .toLowerCase()
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
}

function hojeTexto() {
  const hoje = new Date()
  const ano = hoje.getFullYear()
  const mes = String(hoje.getMonth() + 1).padStart(2, '0')
  const dia = String(hoje.getDate()).padStart(2, '0')
  return `${ano}-${mes}-${dia}`
}

function ehHoje(textoDataHora) {
  return Boolean(textoDataHora) && textoDataHora.slice(0, 10) === hojeTexto()
}

function formatarData(texto) {
  if (!texto) return '—'
  const [ano, mes, dia] = texto.slice(0, 10).split('-')
  return `${dia}/${mes}/${ano}`
}

function textoDias(dias) {
  if (dias === 0) return 'vence hoje'
  if (dias === 1) return 'falta 1 dia'
  if (dias < 0) return `vencido há ${Math.abs(dias)} dia${dias === -1 ? '' : 's'}`
  return `faltam ${dias} dias`
}

function orientadorPrincipal(alerta) {
  return (alerta.orientadores || []).find((o) => o.tipo_orientacao === 'ORIENTADOR') || null
}

function coorientadores(alerta) {
  return (alerta.orientadores || []).filter((o) => o.tipo_orientacao === 'COORIENTADOR')
}

function textoCoorientadores(quantidade) {
  return `+${quantidade} coorientador${quantidade > 1 ? 'es' : ''}`
}

// Texto que aparece ao passar o mouse: quem vai em cópia (CC).
function dicaCopia(alerta) {
  const orientadores = alerta.orientadores || []
  const emails = orientadores.filter((o) => o.email).map((o) => o.email)
  const semEmail = orientadores.filter((o) => !o.email).map((o) => o.nome_professor)

  let dica = `Cópia (CC): ${emails.length ? emails.join(', ') : 'nenhum e-mail cadastrado'}`
  if (semEmail.length) dica += ` · Sem e-mail: ${semEmail.join(', ')}`
  return dica
}

function agruparPorNivel(lista) {
  const grupos = { critico: [], atencao: [], preventivo: [] }
  lista.forEach((alerta) => grupos[nivelUrgencia(alerta.dias_restantes)].push(alerta))
  Object.values(grupos).forEach((grupo) =>
    grupo.sort((a, b) => a.dias_restantes - b.dias_restantes),
  )
  return grupos
}

// ---------- Dados calculados ----------

// Tipos de prazo que aparecem nos alertas (para o filtro).
const tiposDePrazo = computed(() => {
  const mapa = new Map()
  pendentes.value.forEach((a) => mapa.set(a.id_tipo_prazo, a.nome_prazo))
  return [...mapa]
    .map(([id, nome]) => ({ id, nome }))
    .sort((a, b) => a.nome.localeCompare(b.nome, 'pt-BR'))
})

const temFiltro = computed(
  () => busca.value.trim() !== '' || filtroTipo.value !== '' || filtroBolsista.value !== '',
)

const pendentesFiltrados = computed(() => {
  const termo = normalizar(busca.value.trim())
  return pendentes.value.filter((a) => {
    if (
      termo &&
      !normalizar(a.nome_discente).includes(termo) &&
      !normalizar(a.matricula).includes(termo)
    ) {
      return false
    }
    if (filtroTipo.value !== '' && a.id_tipo_prazo !== filtroTipo.value) return false
    if (filtroBolsista.value === 'sim' && !a.eh_bolsista) return false
    if (filtroBolsista.value === 'nao' && a.eh_bolsista) return false
    return true
  })
})

// Cards: total geral. Abas e tabela: com os filtros aplicados.
const totaisPorNivel = computed(() => agruparPorNivel(pendentes.value))
const filtradosPorNivel = computed(() => agruparPorNivel(pendentesFiltrados.value))
const alertasDaAba = computed(() => filtradosPorNivel.value[abaAtiva.value] || [])

const enviadosHoje = computed(
  () => historico.value.filter((h) => h.status === 'ENVIADO' && ehHoje(h.data_envio)).length,
)

function limparFiltros() {
  busca.value = ''
  filtroTipo.value = ''
  filtroBolsista.value = ''
}

async function carregar() {
  carregando.value = true
  erro.value = ''
  try {
    const [listaPendentes, listaHistorico] = await Promise.all([
      buscarAlertasPendentes(),
      buscarHistoricoAlertas(),
    ])
    pendentes.value = listaPendentes
    historico.value = listaHistorico
  } catch {
    erro.value = 'Não foi possível carregar os alertas. Tente de novo em instantes.'
  } finally {
    carregando.value = false
  }
}

onMounted(carregar)
</script>

<template>
  <DefaultLayout>
    <div class="mb-8 bg-white p-6 rounded-2xl border border-gray-200 shadow-sm">
      <h2 class="text-2xl font-bold text-gray-900">Central de Alertas</h2>
      <p class="text-sm text-gray-500 mt-1">
        Prazos que precisam de aviso, separados por urgência.
      </p>
    </div>

    <p
      v-if="usandoDadosDeExemplo"
      class="mb-6 px-4 py-3 rounded-xl border border-amber-300 bg-amber-50 text-amber-900 text-sm"
    >
      <strong>Dados de exemplo:</strong> as rotas de alertas do back-end ainda não estão prontas. Os
      alunos abaixo são fictícios.
    </p>

    <p
      v-if="erro"
      class="mb-8 px-4 py-3 rounded-xl border border-rose-200 bg-rose-50 text-rose-700 text-sm"
    >
      {{ erro }}
    </p>

    <!-- Cards de resumo (total geral, sem filtros) -->
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
      <div
        v-for="nivel in niveis"
        :key="nivel.chave"
        class="p-5 rounded-xl border shadow-sm"
        :class="nivel.classeCard"
      >
        <p class="text-xs font-semibold uppercase tracking-wider mb-1" :class="nivel.classeTitulo">
          {{ nivel.rotulo }}
        </p>
        <p class="text-3xl font-extrabold" :class="nivel.classeValor">
          {{ carregando || erro ? '—' : totaisPorNivel[nivel.chave].length }}
        </p>
        <p class="text-xs text-gray-500 mt-1">{{ nivel.descricao }}</p>
      </div>

      <div class="p-5 rounded-xl border border-emerald-200 bg-emerald-50 shadow-sm">
        <p class="text-xs font-semibold uppercase tracking-wider mb-1 text-emerald-800">
          Enviados hoje
        </p>
        <p class="text-3xl font-extrabold text-emerald-600">
          {{ carregando || erro ? '—' : enviadosHoje }}
        </p>
        <p class="text-xs text-gray-500 mt-1">E-mails com status Enviado</p>
      </div>
    </div>

    <section class="bg-white rounded-2xl border border-gray-200 shadow-sm">
      <!-- Filtros rápidos -->
      <div class="flex flex-wrap items-end gap-4 px-6 pt-6">
        <div class="flex flex-col gap-1 grow min-w-[220px]">
          <label for="alertas-busca" class="text-xs font-medium text-gray-600">
            Buscar discente
          </label>
          <input
            id="alertas-busca"
            v-model="busca"
            type="search"
            placeholder="Nome ou matrícula"
            class="px-3 py-2 text-sm border border-gray-300 rounded-md focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
          />
        </div>

        <div class="flex flex-col gap-1">
          <label for="alertas-tipo" class="text-xs font-medium text-gray-600">Tipo de prazo</label>
          <select
            id="alertas-tipo"
            v-model="filtroTipo"
            class="px-3 py-2 text-sm border border-gray-300 rounded-md focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
          >
            <option value="">Todos</option>
            <option v-for="tipo in tiposDePrazo" :key="tipo.id" :value="tipo.id">
              {{ tipo.nome }}
            </option>
          </select>
        </div>

        <div class="flex flex-col gap-1">
          <label for="alertas-bolsista" class="text-xs font-medium text-gray-600">Bolsa</label>
          <select
            id="alertas-bolsista"
            v-model="filtroBolsista"
            class="px-3 py-2 text-sm border border-gray-300 rounded-md focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
          >
            <option value="">Todos</option>
            <option value="sim">Bolsistas</option>
            <option value="nao">Não bolsistas</option>
          </select>
        </div>

        <button
          v-if="temFiltro"
          type="button"
          class="px-3 py-2 text-sm font-medium text-blue-700 hover:underline"
          @click="limparFiltros"
        >
          Limpar filtros
        </button>
      </div>

      <!-- Abas por urgência (contagem com os filtros) -->
      <div class="flex flex-wrap gap-1 px-4 pt-4 mt-2 border-b border-gray-200" role="tablist">
        <button
          v-for="nivel in niveis"
          :key="nivel.chave"
          type="button"
          role="tab"
          :aria-selected="abaAtiva === nivel.chave"
          class="px-4 py-2 text-sm font-medium border-b-2 -mb-px transition-colors"
          :class="
            abaAtiva === nivel.chave
              ? nivel.classeAba
              : 'border-transparent text-gray-500 hover:text-gray-800'
          "
          @click="abaAtiva = nivel.chave"
        >
          {{ nivel.rotulo }}
          <span class="ml-1 text-xs text-gray-400">
            ({{ carregando ? '…' : filtradosPorNivel[nivel.chave].length }})
          </span>
        </button>
      </div>

      <p v-if="carregando" class="p-6 text-sm italic text-gray-500">Carregando alertas...</p>
      <p v-else-if="erro" class="p-6 text-sm italic text-gray-500">—</p>
      <p v-else-if="alertasDaAba.length === 0" class="p-6 text-sm italic text-gray-500">
        {{
          temFiltro ? 'Nenhum alerta encontrado com esses filtros.' : 'Nenhum alerta neste nível.'
        }}
      </p>

      <!-- Tabela de alertas pendentes -->
      <div v-else class="overflow-x-auto">
        <table class="w-full text-sm">
          <thead class="bg-gray-50 text-left text-gray-700">
            <tr>
              <th class="px-6 py-3 font-semibold">Discente</th>
              <th class="px-6 py-3 font-semibold">Orientador</th>
              <th class="px-6 py-3 font-semibold">Tipo de prazo</th>
              <th class="px-6 py-3 font-semibold">Data limite</th>
              <th class="px-6 py-3 font-semibold">Dias restantes</th>
              <th class="px-6 py-3 font-semibold">Gatilho</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="alerta in alertasDaAba"
              :key="alerta.id_alerta"
              class="border-t border-gray-200 align-top"
            >
              <td class="px-6 py-3">
                <p class="font-medium text-gray-900">{{ alerta.nome_discente }}</p>
                <p class="text-xs text-gray-500">
                  {{ alerta.matricula }}
                  <span
                    v-if="!alerta.email"
                    class="ml-1 inline-block px-2 py-0.5 rounded-full bg-rose-100 text-rose-700 font-semibold"
                  >
                    sem e-mail
                  </span>
                </p>
              </td>
              <td class="px-6 py-3 text-gray-700">
                <p>{{ orientadorPrincipal(alerta)?.nome_professor || '—' }}</p>
                <span
                  v-if="coorientadores(alerta).length"
                  class="mt-1 inline-block px-2 py-0.5 rounded-full bg-gray-100 text-gray-600 text-xs cursor-help"
                  :title="dicaCopia(alerta)"
                >
                  {{ textoCoorientadores(coorientadores(alerta).length) }}
                </span>
              </td>
              <td class="px-6 py-3 text-gray-700">{{ alerta.nome_prazo }}</td>
              <td class="px-6 py-3 text-gray-700 whitespace-nowrap">
                {{ formatarData(alerta.data_limite) }}
              </td>
              <td class="px-6 py-3">
                <span
                  class="inline-block px-2.5 py-1 rounded-full text-xs font-semibold whitespace-nowrap"
                  :class="classeSeloDias(alerta.dias_restantes)"
                >
                  {{ textoDias(alerta.dias_restantes) }}
                </span>
              </td>
              <td class="px-6 py-3 text-gray-600 whitespace-nowrap">
                {{ alerta.dias_antecedencia }} dias antes
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>
  </DefaultLayout>
</template>
