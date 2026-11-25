<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import DefaultLayout from '../layouts/DefaultLayout.vue'
import { buscarSemestres, analisarArquivoDiscentes } from '../services/importacao'

const semestres = ref([])
const carregandoSemestres = ref(true)
const erroSemestres = ref('')
const idSemestre = ref('')

const arquivo = ref(null)
const erroArquivo = ref('')
const arrastando = ref(false)
const campoArquivo = ref(null)

const analisando = ref(false)
const erroAnalise = ref('')
const resultado = ref(null)

// ---------- Semestres ----------

// Mais recente primeiro (ex.: 2026.2, 2026.1, 2025.2...).
const semestresOrdenados = computed(() =>
  [...semestres.value].sort((a, b) =>
    String(b.codigo_semestre).localeCompare(String(a.codigo_semestre), 'pt-BR'),
  ),
)

const semestreEscolhido = computed(
  () => semestres.value.find((s) => s.id_semestre === idSemestre.value) || null,
)

// Sem data_inicio_real o back não consegue calcular os prazos dos alunos.
const semestreSemData = computed(
  () => Boolean(semestreEscolhido.value) && !semestreEscolhido.value.data_inicio_real,
)

function formatarData(texto) {
  if (!texto) return ''
  const [ano, mes, dia] = String(texto).slice(0, 10).split('-')
  return `${dia}/${mes}/${ano}`
}

function rotuloSemestre(semestre) {
  return semestre.data_inicio_real
    ? `${semestre.codigo_semestre} (início em ${formatarData(semestre.data_inicio_real)})`
    : `${semestre.codigo_semestre} (sem data de início real)`
}

async function carregarSemestres() {
  carregandoSemestres.value = true
  erroSemestres.value = ''
  try {
    semestres.value = await buscarSemestres()
  } catch (e) {
    erroSemestres.value = e?.message || 'Não foi possível carregar os semestres.'
  } finally {
    carregandoSemestres.value = false
  }
}

// ---------- Arquivo ----------

// 2048 → "2 KB"; 1572864 → "1,5 MB"
function formatarTamanho(bytes) {
  if (bytes < 1024) return `${bytes} bytes`
  const opcoes = { maximumFractionDigits: 1 }
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toLocaleString('pt-BR', opcoes)} KB`
  return `${(bytes / (1024 * 1024)).toLocaleString('pt-BR', opcoes)} MB`
}

function ehCsv(arquivoEscolhido) {
  return arquivoEscolhido.name.toLowerCase().endsWith('.csv')
}

function limparResultado() {
  resultado.value = null
  erroAnalise.value = ''
}

// Usado tanto pelo clique (seletor do sistema) quanto pelo arrastar e soltar.
function receberArquivos(lista) {
  erroArquivo.value = ''
  if (!lista || lista.length === 0) return
  if (lista.length > 1) {
    erroArquivo.value = 'Envie apenas um arquivo por vez.'
    return
  }
  const escolhido = lista[0]
  if (!ehCsv(escolhido)) {
    erroArquivo.value = `"${escolhido.name}" não é um arquivo .csv. Exporte a planilha do SIGAA como CSV e tente de novo.`
    return
  }
  if (escolhido.size === 0) {
    erroArquivo.value = `"${escolhido.name}" está vazio.`
    return
  }
  arquivo.value = escolhido
  limparResultado()
}

function abrirSeletor() {
  if (analisando.value) return
  campoArquivo.value?.click()
}

function aoSelecionar(evento) {
  receberArquivos(evento.target.files)
  evento.target.value = '' // permite escolher o mesmo arquivo de novo depois de remover
}

// Só "sai" da área quando o mouse vai para fora dela (e não para um elemento de dentro).
function aoSairDaArea(evento) {
  if (!evento.currentTarget.contains(evento.relatedTarget)) arrastando.value = false
}

function aoSoltar(evento) {
  arrastando.value = false
  if (analisando.value) return
  receberArquivos(evento.dataTransfer?.files)
}

function removerArquivo() {
  arquivo.value = null
  erroArquivo.value = ''
  limparResultado()
}

// Se o arquivo for solto fora da área, o navegador abriria o arquivo numa aba nova.
// Enquanto esta página estiver aberta, isso fica bloqueado.
function impedirAberturaDoArquivo(evento) {
  evento.preventDefault()
}

// ---------- Análise ----------

// Critério de aceite: só analisa com semestre válido e arquivo .csv anexado.
const motivoBloqueio = computed(() => {
  if (carregandoSemestres.value) return 'Carregando os semestres...'
  if (!semestreEscolhido.value) return 'Escolha o período de ingresso.'
  if (semestreSemData.value) return 'O semestre escolhido não tem data de início real.'
  if (!arquivo.value) return 'Anexe o arquivo .csv.'
  return ''
})

const podeAnalisar = computed(() => !motivoBloqueio.value && !analisando.value)

async function analisar() {
  if (!podeAnalisar.value) return
  analisando.value = true
  limparResultado()
  try {
    resultado.value = await analisarArquivoDiscentes(arquivo.value, idSemestre.value)
  } catch (e) {
    erroAnalise.value = e?.message || 'Não foi possível analisar o arquivo.'
  } finally {
    analisando.value = false
  }
}

// O back devolve as listas; se vierem só os totais, usa os totais.
function quantidade(lista, total) {
  if (Array.isArray(lista)) return lista.length
  return Number(total) || 0
}

const resumo = computed(() => {
  const r = resultado.value
  if (!r) return null
  return {
    novos: quantidade(r.novos, r.total_novos),
    jaCadastrados: quantidade(r.ja_cadastrados, r.total_ja_cadastrados),
    comErro: quantidade(r.com_erro, r.total_com_erro),
  }
})

onMounted(() => {
  carregarSemestres()
  window.addEventListener('dragover', impedirAberturaDoArquivo)
  window.addEventListener('drop', impedirAberturaDoArquivo)
})

onUnmounted(() => {
  window.removeEventListener('dragover', impedirAberturaDoArquivo)
  window.removeEventListener('drop', impedirAberturaDoArquivo)
})
</script>

<template>
  <DefaultLayout>
    <div class="mb-8 bg-white p-6 rounded-2xl border border-gray-200 shadow-sm">
      <h2 class="text-2xl font-bold text-gray-900">Importar discentes</h2>
      <p class="text-sm text-gray-500 mt-1">
        Cadastre novos alunos a partir do arquivo CSV exportado do SIGAA.
      </p>
    </div>

    <section class="flex flex-col gap-8 bg-white p-6 rounded-2xl border border-gray-200 shadow-sm">
      <!-- ===== 1. Período de ingresso ===== -->
      <div class="flex flex-col gap-2">
        <label for="importacao-semestre" class="text-sm font-semibold text-gray-900">
          1. Período de ingresso <span class="text-rose-600">*</span>
        </label>
        <p class="text-xs text-gray-500">
          Semestre em que os alunos do arquivo entraram no programa. Ele define os prazos de cada
          um.
        </p>

        <p v-if="carregandoSemestres" class="text-sm italic text-gray-500">
          Carregando semestres...
        </p>
        <p
          v-else-if="erroSemestres"
          class="px-4 py-3 rounded-xl border border-rose-200 bg-rose-50 text-rose-700 text-sm"
        >
          {{ erroSemestres }}
        </p>
        <p
          v-else-if="semestres.length === 0"
          class="px-4 py-3 rounded-xl border border-amber-300 bg-amber-50 text-amber-900 text-sm"
        >
          Nenhum semestre cadastrado. Cadastre o semestre em
          <router-link to="/semestres" class="font-medium underline">
            Configurações › Semestres
          </router-link>
          antes de importar.
        </p>
        <select
          v-else
          id="importacao-semestre"
          v-model="idSemestre"
          required
          :disabled="analisando"
          class="max-w-md px-3 py-2 text-sm border border-gray-300 rounded-md bg-white focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100 disabled:bg-gray-100"
          @change="limparResultado"
        >
          <option value="" disabled>Selecione o semestre</option>
          <option
            v-for="semestre in semestresOrdenados"
            :key="semestre.id_semestre"
            :value="semestre.id_semestre"
          >
            {{ rotuloSemestre(semestre) }}
          </option>
        </select>

        <p
          v-if="semestreSemData"
          class="max-w-2xl px-4 py-3 rounded-xl border border-amber-300 bg-amber-50 text-amber-900 text-sm"
        >
          O semestre <strong>{{ semestreEscolhido.codigo_semestre }}</strong> não tem data de início
          real cadastrada. Essa data é usada para calcular os prazos dos alunos, então a importação
          fica bloqueada. Cadastre a data em
          <router-link to="/semestres" class="font-medium underline">
            Configurações › Semestres
          </router-link>
          e volte aqui.
        </p>
      </div>

      <!-- ===== 2. Arquivo CSV ===== -->
      <div class="flex flex-col gap-2">
        <p class="text-sm font-semibold text-gray-900">
          2. Arquivo CSV <span class="text-rose-600">*</span>
        </p>
        <p class="text-xs text-gray-500">
          O arquivo precisa ter as colunas Matrícula, Nome, Curso e Status.
        </p>

        <!-- Arquivo escolhido: nome, tamanho, trocar e remover -->
        <div
          v-if="arquivo"
          class="flex flex-wrap items-center gap-4 px-4 py-3 rounded-xl border border-gray-200 bg-gray-50"
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            class="h-8 w-8 shrink-0 text-blue-600"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            aria-hidden="true"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="1.5"
              d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
            />
          </svg>
          <div class="min-w-0 grow">
            <p class="text-sm font-medium text-gray-900 break-all">{{ arquivo.name }}</p>
            <p class="text-xs text-gray-500">{{ formatarTamanho(arquivo.size) }}</p>
          </div>
          <div class="flex gap-2">
            <button
              type="button"
              class="px-3 py-1.5 text-xs font-medium text-blue-700 border border-blue-200 rounded-md hover:bg-blue-50 disabled:opacity-50 disabled:cursor-not-allowed"
              :disabled="analisando"
              @click="abrirSeletor"
            >
              Trocar arquivo
            </button>
            <button
              type="button"
              class="px-3 py-1.5 text-xs font-medium text-rose-700 border border-rose-200 rounded-md hover:bg-rose-50 disabled:opacity-50 disabled:cursor-not-allowed"
              :disabled="analisando"
              @click="removerArquivo"
            >
              Remover
            </button>
          </div>
        </div>

        <!-- Área de arrastar e soltar (também abre o seletor com clique ou teclado) -->
        <div
          v-else
          role="button"
          tabindex="0"
          aria-label="Escolher arquivo CSV"
          class="flex flex-col items-center justify-center gap-2 px-6 py-10 rounded-xl border-2 border-dashed text-center cursor-pointer transition-colors focus:outline-none focus:ring-2 focus:ring-blue-200"
          :class="
            arrastando
              ? 'border-blue-500 bg-blue-50'
              : 'border-gray-300 bg-gray-50 hover:border-blue-400 hover:bg-blue-50/40'
          "
          @click="abrirSeletor"
          @keydown.enter.prevent="abrirSeletor"
          @keydown.space.prevent="abrirSeletor"
          @dragenter.prevent="arrastando = true"
          @dragover.prevent="arrastando = true"
          @dragleave.prevent="aoSairDaArea"
          @drop.prevent="aoSoltar"
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            class="h-10 w-10"
            :class="arrastando ? 'text-blue-600' : 'text-gray-400'"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            aria-hidden="true"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="1.5"
              d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12"
            />
          </svg>
          <p class="text-sm text-gray-700">
            <span class="font-semibold text-blue-700">Clique para escolher</span>
            ou arraste o arquivo para cá
          </p>
          <p class="text-xs text-gray-500">Somente arquivos .csv</p>
        </div>

        <!-- O seletor de arquivos do sistema fica escondido; a área e o "Trocar" abrem ele -->
        <input
          ref="campoArquivo"
          type="file"
          accept=".csv,text/csv"
          class="hidden"
          @change="aoSelecionar"
        />

        <p v-if="erroArquivo" class="text-sm text-rose-600">{{ erroArquivo }}</p>
      </div>

      <!-- ===== Analisar ===== -->
      <div class="flex flex-wrap items-center gap-4 pt-6 border-t border-gray-200">
        <button
          type="button"
          class="inline-flex items-center gap-2 px-5 py-2.5 text-sm font-semibold text-white bg-blue-600 rounded-md hover:bg-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
          :disabled="!podeAnalisar"
          @click="analisar"
        >
          <svg
            v-if="analisando"
            class="h-4 w-4 animate-spin"
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
            aria-hidden="true"
          >
            <circle
              class="opacity-25"
              cx="12"
              cy="12"
              r="10"
              stroke="currentColor"
              stroke-width="4"
            />
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z" />
          </svg>
          {{ analisando ? 'Analisando arquivo...' : 'Analisar arquivo' }}
        </button>
        <p v-if="motivoBloqueio && !analisando" class="text-sm text-gray-500">
          {{ motivoBloqueio }}
        </p>
      </div>

      <p
        v-if="erroAnalise"
        class="px-4 py-3 rounded-xl border border-rose-200 bg-rose-50 text-rose-700 text-sm"
        role="alert"
      >
        {{ erroAnalise }}
      </p>

      <!-- Resumo da análise (nada foi gravado ainda) -->
      <div
        v-if="resumo"
        class="flex flex-col gap-4 px-5 py-4 rounded-xl border border-emerald-200 bg-emerald-50"
        role="status"
      >
        <p class="text-sm font-semibold text-emerald-900">
          Arquivo analisado. Nada foi gravado no sistema ainda.
        </p>
        <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div class="p-4 rounded-lg bg-white border border-emerald-100">
            <p class="text-xs font-semibold uppercase tracking-wider text-gray-500">Novos</p>
            <p class="text-2xl font-extrabold text-gray-900">{{ resumo.novos }}</p>
          </div>
          <div class="p-4 rounded-lg bg-white border border-emerald-100">
            <p class="text-xs font-semibold uppercase tracking-wider text-gray-500">
              Já cadastrados
            </p>
            <p class="text-2xl font-extrabold text-gray-900">{{ resumo.jaCadastrados }}</p>
          </div>
          <div class="p-4 rounded-lg bg-white border border-emerald-100">
            <p class="text-xs font-semibold uppercase tracking-wider text-gray-500">Com erro</p>
            <p class="text-2xl font-extrabold text-gray-900">{{ resumo.comErro }}</p>
          </div>
        </div>
      </div>
    </section>
  </DefaultLayout>
</template>
