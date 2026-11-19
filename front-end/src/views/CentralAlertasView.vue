<script setup>
import { ref, computed, onMounted } from 'vue'
import DefaultLayout from '../layouts/DefaultLayout.vue'
import { buscarAlertasPendentes, buscarHistoricoAlertas } from '../services/alertas'

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
  },
  {
    chave: 'atencao',
    rotulo: 'Atenção',
    descricao: 'De 8 a 30 dias',
    classeCard: 'bg-amber-50 border-amber-200',
    classeTitulo: 'text-amber-800',
    classeValor: 'text-amber-600',
    classeAba: 'border-amber-500 text-amber-800',
  },
  {
    chave: 'preventivo',
    rotulo: 'Preventivo',
    descricao: 'Mais de 30 dias',
    classeCard: 'bg-blue-50 border-blue-200',
    classeTitulo: 'text-blue-800',
    classeValor: 'text-blue-600',
    classeAba: 'border-blue-500 text-blue-800',
  },
]

const pendentes = ref([])
const historico = ref([])
const carregando = ref(true)
const erro = ref('')
const abaAtiva = ref('critico')

function nivelUrgencia(dias) {
  if (dias <= 7) return 'critico'
  if (dias <= 30) return 'atencao'
  return 'preventivo'
}

function ehHoje(textoDataHora) {
  if (!textoDataHora) return false
  const hoje = new Date()
  const ano = hoje.getFullYear()
  const mes = String(hoje.getMonth() + 1).padStart(2, '0')
  const dia = String(hoje.getDate()).padStart(2, '0')
  return textoDataHora.slice(0, 10) === `${ano}-${mes}-${dia}`
}

function textoDias(dias) {
  if (dias === 0) return 'vence hoje'
  if (dias === 1) return 'falta 1 dia'
  if (dias < 0) return `vencido há ${Math.abs(dias)} dia${dias === -1 ? '' : 's'}`
  return `faltam ${dias} dias`
}

// Alertas separados por nível, do mais urgente para o menos urgente.
const pendentesPorNivel = computed(() => {
  const grupos = { critico: [], atencao: [], preventivo: [] }
  pendentes.value.forEach((alerta) => grupos[nivelUrgencia(alerta.dias_restantes)].push(alerta))
  Object.values(grupos).forEach((lista) =>
    lista.sort((a, b) => a.dias_restantes - b.dias_restantes),
  )
  return grupos
})

const enviadosHoje = computed(
  () => historico.value.filter((h) => h.status === 'ENVIADO' && ehHoje(h.data_envio)).length,
)

const alertasDaAba = computed(() => pendentesPorNivel.value[abaAtiva.value] || [])

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
      v-if="erro"
      class="mb-8 px-4 py-3 rounded-xl border border-rose-200 bg-rose-50 text-rose-700 text-sm"
    >
      {{ erro }}
    </p>

    <!-- Cards de resumo -->
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
          {{ carregando || erro ? '—' : pendentesPorNivel[nivel.chave].length }}
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

    <!-- Abas por urgência -->
    <section class="bg-white rounded-2xl border border-gray-200 shadow-sm">
      <div class="flex flex-wrap gap-1 px-4 pt-4 border-b border-gray-200" role="tablist">
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
            ({{ carregando ? '…' : pendentesPorNivel[nivel.chave].length }})
          </span>
        </button>
      </div>

      <div class="p-6">
        <p v-if="carregando" class="text-sm italic text-gray-500">Carregando alertas...</p>
        <p v-else-if="erro" class="text-sm italic text-gray-500">—</p>
        <p v-else-if="alertasDaAba.length === 0" class="text-sm italic text-gray-500">
          Nenhum alerta neste nível.
        </p>
        <!-- Lista simples por enquanto: a tabela completa vem no próximo passo -->
        <ul v-else class="divide-y divide-gray-100">
          <li
            v-for="alerta in alertasDaAba"
            :key="alerta.id_alerta"
            class="py-3 flex flex-wrap items-center justify-between gap-2 text-sm"
          >
            <span class="font-medium text-gray-900">
              {{ alerta.nome_discente }}
              <span class="font-normal text-gray-500">— {{ alerta.nome_prazo }}</span>
            </span>
            <span class="text-gray-600">{{ textoDias(alerta.dias_restantes) }}</span>
          </li>
        </ul>
      </div>
    </section>
  </DefaultLayout>
</template>
