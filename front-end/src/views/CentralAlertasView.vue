<script setup>
import { ref, computed, onMounted } from 'vue'
import DefaultLayout from '../layouts/DefaultLayout.vue'
import BaseModal from '../components/BaseModal.vue'
import BaseButton from '../components/BaseButton.vue'
import {
  buscarAlertasPendentes,
  buscarHistoricoAlertas,
  reenviarAlerta,
  usandoDadosDeExemplo,
} from '../services/alertas'

// Níveis de urgência, como na task:
// crítico = vencido ou até 7 dias; atenção = 8 a 30; preventivo = mais de 30.
// Visual dos cards igual ao Dashboard: só o crítico fica com fundo colorido.
const niveis = [
  {
    chave: 'critico',
    rotulo: 'Crítico',
    descricao: 'Vencidos ou até 7 dias',
    destaque: true,
    classeAba: 'border-rose-500 text-rose-700',
    classeSelo: 'bg-rose-100 text-rose-700',
  },
  {
    chave: 'atencao',
    rotulo: 'Atenção',
    descricao: 'De 8 a 30 dias',
    destaque: false,
    classeAba: 'border-amber-500 text-amber-800',
    classeSelo: 'bg-amber-100 text-amber-800',
  },
  {
    chave: 'preventivo',
    rotulo: 'Preventivo',
    descricao: 'Mais de 30 dias',
    destaque: false,
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

// Seleção (guarda os id_alerta marcados, em qualquer aba)
const selecionados = ref([])

// Reenvio: guarda quais envios estão sendo reenviados (para desativar o botão)
const reenviando = ref({})

// Aviso que aparece no canto da tela por alguns segundos
const aviso = ref(null)
let temporizadorAviso = null

// Modal provisório: será trocado pelo modal da PAP-49 (edição das minutas)
const modalMinutasAberto = ref(false)
const alertasParaMinuta = ref([])

const naAbaHistorico = computed(() => abaAtiva.value === 'historico')

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

// "Ana Clara Lima" → "AL" (primeira letra do primeiro e do último nome).
function iniciais(nome) {
  const partes = String(nome ?? '')
    .trim()
    .split(/\s+/)
    .filter(Boolean)
  if (partes.length === 0) return '?'
  const primeira = partes[0][0]
  const ultima = partes.length > 1 ? partes[partes.length - 1][0] : ''
  return `${primeira}${ultima}`.toUpperCase()
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

// "2026-11-19T09:17:00" → "19/11/2026 às 09:17"
function formatarDataHora(texto) {
  if (!texto) return '—'
  const hora = texto.slice(11, 16)
  return hora ? `${formatarData(texto)} às ${hora}` : formatarData(texto)
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

function mostrarAviso(texto, tipo) {
  aviso.value = { texto, tipo }
  clearTimeout(temporizadorAviso)
  temporizadorAviso = setTimeout(() => {
    aviso.value = null
  }, 3000)
}

// ---------- Dados calculados: pendentes ----------

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

// ---------- Dados calculados: histórico ----------

const enviadosHoje = computed(
  () => historico.value.filter((h) => h.status === 'ENVIADO' && ehHoje(h.data_envio)).length,
)

// No histórico, só a busca vale (nome, matrícula ou e-mail). Mais recente primeiro.
const historicoFiltrado = computed(() => {
  const termo = normalizar(busca.value.trim())
  return historico.value
    .filter(
      (h) =>
        !termo ||
        normalizar(h.nome_discente).includes(termo) ||
        normalizar(h.matricula).includes(termo) ||
        normalizar(h.destinatario_email).includes(termo),
    )
    .sort((a, b) => String(b.data_envio).localeCompare(String(a.data_envio)))
})

// ---------- Seleção ----------

function estaSelecionado(alerta) {
  return selecionados.value.includes(alerta.id_alerta)
}

function alternarSelecao(alerta) {
  selecionados.value = estaSelecionado(alerta)
    ? selecionados.value.filter((id) => id !== alerta.id_alerta)
    : [...selecionados.value, alerta.id_alerta]
}

const quantosDaAbaSelecionados = computed(
  () => alertasDaAba.value.filter((a) => estaSelecionado(a)).length,
)
const todosDaAbaSelecionados = computed(
  () =>
    alertasDaAba.value.length > 0 && quantosDaAbaSelecionados.value === alertasDaAba.value.length,
)
// "Meio marcado": alguns da aba marcados, mas não todos.
const algunsDaAbaSelecionados = computed(
  () => quantosDaAbaSelecionados.value > 0 && !todosDaAbaSelecionados.value,
)

function alternarTodosDaAba() {
  const idsDaAba = alertasDaAba.value.map((a) => a.id_alerta)
  if (todosDaAbaSelecionados.value) {
    selecionados.value = selecionados.value.filter((id) => !idsDaAba.includes(id))
  } else {
    selecionados.value = [...new Set([...selecionados.value, ...idsDaAba])]
  }
}

function limparSelecao() {
  selecionados.value = []
}

const alertasSelecionados = computed(() =>
  pendentes.value.filter((a) => selecionados.value.includes(a.id_alerta)),
)

// ---------- Ações ----------

function abrirMinutas(alertas) {
  alertasParaMinuta.value = alertas
  modalMinutasAberto.value = true
}

function fecharMinutas() {
  modalMinutasAberto.value = false
}

async function reenviar(envio) {
  reenviando.value[envio.id_historico] = true
  try {
    const atualizado = await reenviarAlerta(envio.id_historico)
    historico.value = historico.value.map((h) =>
      h.id_historico === atualizado.id_historico ? atualizado : h,
    )
    mostrarAviso(`Alerta reenviado para ${envio.nome_discente}.`, 'sucesso')
  } catch {
    mostrarAviso('Não foi possível reenviar o alerta. Tente de novo.', 'erro')
  } finally {
    reenviando.value[envio.id_historico] = false
  }
}

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
    // Tira da seleção os alertas que não existem mais (por exemplo, já enviados).
    const idsExistentes = listaPendentes.map((a) => a.id_alerta)
    selecionados.value = selecionados.value.filter((id) => idsExistentes.includes(id))
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
    <!-- Aviso no canto da tela (some depois de 3 segundos) -->
    <div
      v-if="aviso"
      class="fixed top-20 right-6 z-50 px-4 py-3 rounded-lg border text-sm shadow-lg"
      :class="
        aviso.tipo === 'sucesso'
          ? 'bg-emerald-50 border-emerald-200 text-emerald-800'
          : 'bg-rose-50 border-rose-200 text-rose-700'
      "
      role="status"
    >
      {{ aviso.texto }}
    </div>

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

    <!-- Cards de resumo (total geral, sem filtros), no mesmo estilo do Dashboard -->
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
      <div
        v-for="nivel in niveis"
        :key="nivel.chave"
        class="p-5 rounded-xl border shadow-sm"
        :class="nivel.destaque ? 'bg-rose-50 border-rose-200' : 'bg-white border-gray-200'"
      >
        <p
          class="text-xs font-semibold uppercase tracking-wider mb-1"
          :class="nivel.destaque ? 'text-rose-700' : 'text-gray-500'"
        >
          {{ nivel.rotulo }}
        </p>
        <p
          class="text-3xl font-extrabold"
          :class="nivel.destaque ? 'text-rose-600' : 'text-gray-900'"
        >
          {{ carregando || erro ? '—' : totaisPorNivel[nivel.chave].length }}
        </p>
        <p class="text-xs text-gray-500 mt-1">{{ nivel.descricao }}</p>
      </div>

      <div class="p-5 rounded-xl border border-gray-200 bg-white shadow-sm">
        <p class="text-xs font-semibold uppercase tracking-wider mb-1 text-gray-500">
          Enviados hoje
        </p>
        <p class="text-3xl font-extrabold text-gray-900">
          {{ carregando || erro ? '—' : enviadosHoje }}
        </p>
        <p class="text-xs text-gray-500 mt-1">E-mails com status Enviado</p>
      </div>
    </div>

    <section
      class="bg-white rounded-2xl border border-gray-200 shadow-sm"
      :class="{ 'mb-24': selecionados.length > 0 }"
    >
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
            :placeholder="naAbaHistorico ? 'Nome, matrícula ou e-mail' : 'Nome ou matrícula'"
            class="px-3 py-2 text-sm border border-gray-300 rounded-md focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
          />
        </div>

        <!-- Tipo de prazo e bolsa só fazem sentido nas abas de pendentes -->
        <template v-if="!naAbaHistorico">
          <div class="flex flex-col gap-1">
            <label for="alertas-tipo" class="text-xs font-medium text-gray-600">
              Tipo de prazo
            </label>
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
        </template>

        <button
          v-if="temFiltro"
          type="button"
          class="px-3 py-2 text-sm font-medium text-blue-700 hover:underline"
          @click="limparFiltros"
        >
          Limpar filtros
        </button>
      </div>

      <!-- Abas: três níveis de urgência (contagem com os filtros) + histórico -->
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

        <button
          type="button"
          role="tab"
          :aria-selected="naAbaHistorico"
          class="px-4 py-2 text-sm font-medium border-b-2 -mb-px transition-colors"
          :class="
            naAbaHistorico
              ? 'border-gray-700 text-gray-900'
              : 'border-transparent text-gray-500 hover:text-gray-800'
          "
          @click="abaAtiva = 'historico'"
        >
          Histórico
          <span class="ml-1 text-xs text-gray-400">
            ({{ carregando ? '…' : historicoFiltrado.length }})
          </span>
        </button>
      </div>

      <p v-if="carregando" class="p-6 text-sm italic text-gray-500">Carregando alertas...</p>
      <p v-else-if="erro" class="p-6 text-sm italic text-gray-500">—</p>

      <!-- ===== Aba Histórico ===== -->
      <template v-else-if="naAbaHistorico">
        <p v-if="historicoFiltrado.length === 0" class="p-6 text-sm italic text-gray-500">
          {{
            busca.trim() ? 'Nenhum envio encontrado com essa busca.' : 'Nenhum envio registrado.'
          }}
        </p>

        <div v-else class="overflow-x-auto">
          <table class="w-full text-sm">
            <thead class="bg-gray-50 text-left text-gray-700 whitespace-nowrap">
              <tr>
                <th class="px-6 py-3 font-semibold">Envio</th>
                <th class="px-4 py-3 font-semibold">Discente</th>
                <th class="px-4 py-3 font-semibold">Prazo</th>
                <th class="px-4 py-3 font-semibold">Destinatários</th>
                <th class="px-4 py-3 font-semibold">Status</th>
                <th class="px-6 py-3 font-semibold text-right">Ações</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="envio in historicoFiltrado"
                :key="envio.id_historico"
                class="border-t border-gray-200 align-middle hover:bg-gray-50 transition-colors"
              >
                <td class="px-6 py-4 text-gray-700 whitespace-nowrap">
                  {{ formatarDataHora(envio.data_envio) }}
                </td>
                <td class="px-4 py-4">
                  <div class="flex items-center gap-3">
                    <span
                      class="h-9 w-9 shrink-0 rounded-full bg-blue-100 text-blue-800 text-xs font-semibold flex items-center justify-center"
                      aria-hidden="true"
                    >
                      {{ iniciais(envio.nome_discente) }}
                    </span>
                    <div>
                      <p class="font-medium text-gray-900 leading-snug">
                        {{ envio.nome_discente }}
                      </p>
                      <p class="mt-0.5 text-xs text-gray-500">{{ envio.matricula }}</p>
                    </div>
                  </div>
                </td>
                <td class="px-4 py-4 text-gray-700">{{ envio.nome_prazo }}</td>
                <td class="px-4 py-4 text-gray-700">
                  <p class="leading-snug">{{ envio.destinatario_email || '—' }}</p>
                  <p v-if="envio.emails_cc" class="mt-0.5 text-xs text-gray-500">
                    Cc: {{ envio.emails_cc }}
                  </p>
                </td>
                <td class="px-4 py-4">
                  <span
                    class="inline-block px-2.5 py-1 rounded-full text-xs font-semibold whitespace-nowrap"
                    :class="
                      envio.status === 'ENVIADO'
                        ? 'bg-emerald-100 text-emerald-800'
                        : 'bg-rose-100 text-rose-700'
                    "
                  >
                    {{ envio.status === 'ENVIADO' ? 'Enviado' : 'Falha' }}
                  </span>
                  <p v-if="envio.mensagem_erro" class="mt-1 text-xs text-rose-600">
                    {{ envio.mensagem_erro }}
                  </p>
                </td>
                <td class="px-6 py-4 text-right">
                  <button
                    v-if="envio.status === 'FALHA'"
                    type="button"
                    class="px-3 py-1.5 text-xs font-medium text-blue-700 border border-blue-200 rounded-md hover:bg-blue-50 whitespace-nowrap disabled:opacity-50 disabled:cursor-not-allowed"
                    :disabled="reenviando[envio.id_historico]"
                    @click="reenviar(envio)"
                  >
                    {{ reenviando[envio.id_historico] ? 'Reenviando...' : 'Reenviar' }}
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </template>

      <!-- ===== Abas de pendentes ===== -->
      <p v-else-if="alertasDaAba.length === 0" class="p-6 text-sm italic text-gray-500">
        {{
          temFiltro ? 'Nenhum alerta encontrado com esses filtros.' : 'Nenhum alerta neste nível.'
        }}
      </p>

      <div v-else class="overflow-x-auto">
        <table class="w-full text-sm">
          <thead class="bg-gray-50 text-left text-gray-700 whitespace-nowrap">
            <tr>
              <th class="pl-6 pr-2 py-3 w-10">
                <input
                  type="checkbox"
                  class="h-4 w-4 cursor-pointer"
                  :checked="todosDaAbaSelecionados"
                  :indeterminate="algunsDaAbaSelecionados"
                  aria-label="Selecionar todos desta aba"
                  @change="alternarTodosDaAba"
                />
              </th>
              <th class="px-4 py-3 font-semibold">Discente</th>
              <th class="px-4 py-3 font-semibold">Orientador</th>
              <th class="px-4 py-3 font-semibold">Tipo de prazo</th>
              <th class="px-4 py-3 font-semibold">Data limite</th>
              <th class="px-4 py-3 font-semibold">Dias restantes</th>
              <th class="px-4 py-3 font-semibold">Gatilho</th>
              <th class="px-6 py-3 font-semibold text-right">Ações</th>
            </tr>
          </thead>
          <tbody>
            <!-- align-middle: as colunas com uma informação só ficam centralizadas na altura da linha -->
            <tr
              v-for="alerta in alertasDaAba"
              :key="alerta.id_alerta"
              class="border-t border-gray-200 align-middle transition-colors"
              :class="estaSelecionado(alerta) ? 'bg-blue-50/50' : 'hover:bg-gray-50'"
            >
              <td class="pl-6 pr-2 py-4">
                <input
                  type="checkbox"
                  class="h-4 w-4 cursor-pointer"
                  :checked="estaSelecionado(alerta)"
                  :aria-label="`Selecionar ${alerta.nome_discente}`"
                  @change="alternarSelecao(alerta)"
                />
              </td>
              <td class="px-4 py-4">
                <div class="flex items-center gap-3">
                  <!-- Iniciais, como na tela de Estudantes -->
                  <span
                    class="h-9 w-9 shrink-0 rounded-full bg-blue-100 text-blue-800 text-xs font-semibold flex items-center justify-center"
                    aria-hidden="true"
                  >
                    {{ iniciais(alerta.nome_discente) }}
                  </span>
                  <div>
                    <p class="font-medium text-gray-900 leading-snug">{{ alerta.nome_discente }}</p>
                    <p class="mt-0.5 text-xs text-gray-500">{{ alerta.matricula }}</p>
                    <!-- Mesmo padrão do "+1 coorientador": linha própria, texto pequeno -->
                    <p
                      v-if="!alerta.email"
                      class="mt-0.5 text-xs font-medium text-rose-600 whitespace-nowrap"
                    >
                      Sem e-mail cadastrado
                    </p>
                  </div>
                </div>
              </td>
              <td class="px-4 py-4 text-gray-700">
                <p class="leading-snug">{{ orientadorPrincipal(alerta)?.nome_professor || '—' }}</p>
                <!-- Discreto, como a matrícula: o mouse em cima mostra quem vai em cópia -->
                <p
                  v-if="coorientadores(alerta).length"
                  class="mt-0.5 text-xs text-gray-500 whitespace-nowrap"
                >
                  <span
                    class="underline decoration-dotted underline-offset-2 cursor-help"
                    :title="dicaCopia(alerta)"
                  >
                    {{ textoCoorientadores(coorientadores(alerta).length) }}
                  </span>
                </p>
              </td>
              <td class="px-4 py-4 text-gray-700">{{ alerta.nome_prazo }}</td>
              <td class="px-4 py-4 text-gray-700 whitespace-nowrap">
                {{ formatarData(alerta.data_limite) }}
              </td>
              <td class="px-4 py-4">
                <span
                  class="inline-block px-2.5 py-1 rounded-full text-xs font-semibold whitespace-nowrap"
                  :class="classeSeloDias(alerta.dias_restantes)"
                >
                  {{ textoDias(alerta.dias_restantes) }}
                </span>
              </td>
              <td class="px-4 py-4 text-gray-600 whitespace-nowrap">
                {{ alerta.dias_antecedencia }} dias antes
              </td>
              <td class="px-6 py-4 text-right">
                <button
                  type="button"
                  class="px-3 py-1.5 text-xs font-medium text-blue-700 border border-blue-200 rounded-md hover:bg-blue-50 whitespace-nowrap"
                  @click="abrirMinutas([alerta])"
                >
                  Revisar e Enviar
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <!-- Barra flutuante de ação em massa (aparece com 1 ou mais selecionados) -->
    <div
      v-if="selecionados.length > 0"
      class="fixed bottom-6 left-1/2 -translate-x-1/2 z-40 flex flex-wrap items-center gap-4 px-5 py-3 bg-gray-900 text-white rounded-xl shadow-lg"
      role="region"
      aria-label="Ações para os alertas selecionados"
    >
      <span class="text-sm">
        <strong>{{ selecionados.length }}</strong>
        selecionado{{ selecionados.length > 1 ? 's' : '' }}
      </span>
      <button
        type="button"
        class="text-sm text-gray-300 hover:text-white hover:underline"
        @click="limparSelecao"
      >
        Limpar seleção
      </button>
      <button
        type="button"
        class="px-4 py-2 text-sm font-semibold bg-blue-600 rounded-md hover:bg-blue-500"
        @click="abrirMinutas(alertasSelecionados)"
      >
        Gerar minutas em lote ({{ selecionados.length }})
      </button>
    </div>

    <!-- Modal PROVISÓRIO: será substituído pelo modal de edição das minutas (PAP-49) -->
    <BaseModal
      :aberto="modalMinutasAberto"
      titulo="Revisar e enviar"
      larguraMaxima="560px"
      @fechar="fecharMinutas"
    >
      <p class="text-sm text-gray-600 mb-4">
        A edição das minutas e o envio dos e-mails entram na próxima etapa (PAP-49). Por enquanto,
        esta janela mostra só os alunos escolhidos.
      </p>
      <ul class="divide-y divide-gray-100 border border-gray-200 rounded-lg">
        <li
          v-for="alerta in alertasParaMinuta"
          :key="alerta.id_alerta"
          class="px-4 py-2 text-sm flex flex-wrap justify-between gap-2"
        >
          <span class="font-medium text-gray-900">{{ alerta.nome_discente }}</span>
          <span class="text-gray-500">
            {{ alerta.nome_prazo }} · {{ textoDias(alerta.dias_restantes) }}
          </span>
        </li>
      </ul>

      <template #rodape>
        <BaseButton type="button" variant="secondary" @click="fecharMinutas">Fechar</BaseButton>
      </template>
    </BaseModal>
  </DefaultLayout>
</template>
