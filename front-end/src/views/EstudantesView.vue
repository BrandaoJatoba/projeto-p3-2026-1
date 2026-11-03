<script setup>
import { ref, computed, watch, onMounted, onBeforeUnmount } from 'vue'
import DefaultLayout from '../layouts/DefaultLayout.vue'
import BaseButton from '../components/BaseButton.vue'
import { useAuthStore } from '../stores/auth'

const authStore = useAuthStore()

const estudantes = ref([])
const total = ref(0)
const carregando = ref(false)
const erro = ref('')

const colunaOrdenacao = ref('nome_discente')
const ordemDesc = ref(false)

const opcoesPorPagina = [10, 25, 50]
const porPagina = ref(10)
const paginaAtual = ref(1)

const termoBusca = ref('')
let temporizadorBusca = null
let ultimaRequisicao = 0

const opcoesStatus = [
  'ATIVO',
  'TRANCADO',
  'PROCESSO DE DESLIGAMENTO',
  'DESLIGADO',
  'PÓS DEFESA',
  'TITULADO',
]
const filtroStatus = ref('')
const filtroSemestre = ref('')
const filtroBolsa = ref('')

const semestres = ref([])

const totalPaginas = computed(() => Math.max(1, Math.ceil(total.value / porPagina.value)))
const inicioIntervalo = computed(() =>
  total.value === 0 ? 0 : (paginaAtual.value - 1) * porPagina.value + 1,
)
const fimIntervalo = computed(
  () => (paginaAtual.value - 1) * porPagina.value + estudantes.value.length,
)
const termoBuscaLimpo = computed(() => termoBusca.value.trim())
const temFiltroAtivo = computed(
  () => filtroStatus.value !== '' || filtroSemestre.value !== '' || filtroBolsa.value !== '',
)
const codigosSemestres = computed(() => {
  const mapa = {}
  for (const semestre of semestres.value) {
    mapa[semestre.id_semestre] = semestre.codigo_semestre
  }
  return mapa
})

const classesStatus = {
  ATIVO: 'status-ativo',
  TRANCADO: 'status-trancado',
  'PROCESSO DE DESLIGAMENTO': 'status-desligamento',
  DESLIGADO: 'status-desligado',
  'PÓS DEFESA': 'status-pos-defesa',
  TITULADO: 'status-titulado',
}

function classeDoStatus(status) {
  return classesStatus[status] || 'status-desligado'
}

function codigoDoSemestre(idSemestre) {
  return codigosSemestres.value[idSemestre] || idSemestre
}

function iniciais(nome) {
  const partes = (nome || '').trim().split(/\s+/).filter(Boolean)
  if (partes.length === 0) return '?'
  const primeira = partes[0][0]
  const ultima = partes.length > 1 ? partes[partes.length - 1][0] : ''
  return (primeira + ultima).toUpperCase()
}

function ordenarPor(coluna) {
  if (colunaOrdenacao.value === coluna) {
    ordemDesc.value = !ordemDesc.value
  } else {
    colunaOrdenacao.value = coluna
    ordemDesc.value = false
  }
  paginaAtual.value = 1
  buscarEstudantes()
}

function indicadorOrdenacao(coluna) {
  if (colunaOrdenacao.value !== coluna) return ''
  return ordemDesc.value ? '▼' : '▲'
}

function irParaPagina(numero) {
  if (numero < 1 || numero > totalPaginas.value) return
  paginaAtual.value = numero
  buscarEstudantes()
}

function mudarPorPagina() {
  paginaAtual.value = 1
  buscarEstudantes()
}

function aplicarFiltros() {
  paginaAtual.value = 1
  buscarEstudantes()
}

function limparFiltros() {
  filtroStatus.value = ''
  filtroSemestre.value = ''
  filtroBolsa.value = ''
  aplicarFiltros()
}

watch(termoBusca, () => {
  clearTimeout(temporizadorBusca)
  temporizadorBusca = setTimeout(() => {
    paginaAtual.value = 1
    buscarEstudantes()
  }, 400)
})

async function buscarSemestres() {
  try {
    const resposta = await fetch('http://localhost:8000/configuracoes/semestres', {
      headers: { Authorization: `Bearer ${authStore.token}` },
    })
    if (!resposta.ok) return
    semestres.value = await resposta.json()
  } catch {
    // Sem a lista de semestres, a tabela mostra o número do semestre.
  }
}

async function buscarEstudantes() {
  const numeroRequisicao = ++ultimaRequisicao
  carregando.value = true
  erro.value = ''
  const parametros = new URLSearchParams({
    ordenar_por: colunaOrdenacao.value,
    ordem_desc: String(ordemDesc.value),
    skip: String((paginaAtual.value - 1) * porPagina.value),
    limit: String(porPagina.value),
  })
  if (termoBuscaLimpo.value) {
    parametros.set('busca', termoBuscaLimpo.value)
  }
  if (filtroStatus.value !== '') {
    parametros.set('status_atual', filtroStatus.value)
  }
  if (filtroSemestre.value !== '') {
    parametros.set('id_semestre', String(filtroSemestre.value))
  }
  if (filtroBolsa.value !== '') {
    parametros.set('eh_bolsista', filtroBolsa.value)
  }
  try {
    const resposta = await fetch(`http://localhost:8000/estudantes?${parametros}`, {
      headers: { Authorization: `Bearer ${authStore.token}` },
    })
    if (numeroRequisicao !== ultimaRequisicao) return
    if (!resposta.ok) {
      if (resposta.status === 401) {
        erro.value = 'Sua sessão expirou. Saia e entre de novo.'
      } else {
        erro.value = `Não foi possível carregar os estudantes (erro ${resposta.status}).`
      }
      return
    }
    const dados = await resposta.json()
    if (numeroRequisicao !== ultimaRequisicao) return
    estudantes.value = dados.itens
    total.value = dados.total
  } catch {
    if (numeroRequisicao !== ultimaRequisicao) return
    erro.value = 'Não foi possível conectar ao servidor. Verifique se o backend está ligado.'
  } finally {
    if (numeroRequisicao === ultimaRequisicao) {
      carregando.value = false
    }
  }
}

onMounted(() => {
  buscarSemestres()
  buscarEstudantes()
})

onBeforeUnmount(() => {
  clearTimeout(temporizadorBusca)
})
</script>

<template>
  <DefaultLayout>
    <div class="page-header">
      <h1>Estudantes</h1>
    </div>

    <div class="barra-ferramentas">
      <input
        v-model="termoBusca"
        type="search"
        class="campo-busca"
        placeholder="Buscar por nome ou matrícula"
        aria-label="Buscar por nome ou matrícula"
        maxlength="100"
      />

      <select
        v-model="filtroStatus"
        class="seletor-filtro"
        aria-label="Filtrar por status"
        @change="aplicarFiltros"
      >
        <option value="">Todos os status</option>
        <option v-for="status in opcoesStatus" :key="status" :value="status">
          {{ status }}
        </option>
      </select>

      <select
        v-model="filtroSemestre"
        class="seletor-filtro"
        aria-label="Filtrar por semestre"
        @change="aplicarFiltros"
      >
        <option value="">Todos os semestres</option>
        <option
          v-for="semestre in semestres"
          :key="semestre.id_semestre"
          :value="semestre.id_semestre"
        >
          {{ semestre.codigo_semestre }}
        </option>
      </select>

      <select
        v-model="filtroBolsa"
        class="seletor-filtro"
        aria-label="Filtrar por bolsa"
        @change="aplicarFiltros"
      >
        <option value="">Bolsistas e não bolsistas</option>
        <option value="true">Só bolsistas</option>
        <option value="false">Só não bolsistas</option>
      </select>

      <BaseButton v-if="temFiltroAtivo" type="button" variant="secondary" @click="limparFiltros">
        Limpar filtros
      </BaseButton>
    </div>

    <div v-if="carregando && estudantes.length === 0" class="estado">Carregando estudantes...</div>

    <div v-else-if="erro" class="aviso-erro">{{ erro }}</div>

    <div v-else-if="estudantes.length === 0" class="estado">
      <template v-if="temFiltroAtivo"
        >Nenhum estudante encontrado com os filtros escolhidos.</template
      >
      <template v-else-if="termoBuscaLimpo">
        Nenhum estudante encontrado para "{{ termoBuscaLimpo }}".
      </template>
      <template v-else>Nenhum estudante cadastrado.</template>
    </div>

    <div v-else class="tabela-card" :class="{ atualizando: carregando }">
      <p class="contagem">
        {{ total }} {{ total === 1 ? 'estudante encontrado' : 'estudantes encontrados' }}
      </p>
      <table class="tabela">
        <thead>
          <tr>
            <th>
              <button type="button" class="botao-ordenar" @click="ordenarPor('nome_discente')">
                Nome <span class="indicador">{{ indicadorOrdenacao('nome_discente') }}</span>
              </button>
            </th>
            <th>
              <button type="button" class="botao-ordenar" @click="ordenarPor('matricula')">
                Matrícula <span class="indicador">{{ indicadorOrdenacao('matricula') }}</span>
              </button>
            </th>
            <th>
              <button type="button" class="botao-ordenar" @click="ordenarPor('id_semestre')">
                Semestre <span class="indicador">{{ indicadorOrdenacao('id_semestre') }}</span>
              </button>
            </th>
            <th>Status</th>
            <th>E-mail</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="estudante in estudantes" :key="estudante.id_estudante">
            <td>
              <div class="celula-nome">
                <span class="avatar">{{ iniciais(estudante.nome_discente) }}</span>
                <span>{{ estudante.nome_discente }}</span>
                <span v-if="estudante.eh_bolsista" class="selo-bolsista">Bolsista</span>
              </div>
            </td>
            <td>{{ estudante.matricula }}</td>
            <td>{{ codigoDoSemestre(estudante.id_semestre) }}</td>
            <td>
              <span class="badge" :class="classeDoStatus(estudante.status_atual)">
                {{ estudante.status_atual }}
              </span>
            </td>
            <td>{{ estudante.email }}</td>
          </tr>
        </tbody>
      </table>

      <div class="paginacao">
        <span class="paginacao-info">
          Mostrando {{ inicioIntervalo }}–{{ fimIntervalo }} de {{ total }}
        </span>
        <div class="paginacao-controles">
          <label class="por-pagina">
            Por página
            <select v-model.number="porPagina" class="seletor" @change="mudarPorPagina">
              <option v-for="opcao in opcoesPorPagina" :key="opcao" :value="opcao">
                {{ opcao }}
              </option>
            </select>
          </label>
          <BaseButton
            type="button"
            variant="secondary"
            :disabled="paginaAtual === 1 || carregando"
            @click="irParaPagina(paginaAtual - 1)"
          >
            Anterior
          </BaseButton>
          <span class="paginacao-pagina">Página {{ paginaAtual }} de {{ totalPaginas }}</span>
          <BaseButton
            type="button"
            variant="secondary"
            :disabled="paginaAtual === totalPaginas || carregando"
            @click="irParaPagina(paginaAtual + 1)"
          >
            Próxima
          </BaseButton>
        </div>
      </div>
    </div>
  </DefaultLayout>
</template>

<style scoped>
.page-header {
  margin-bottom: 24px;
}

.page-header h1 {
  font-size: 1.8rem;
  font-weight: 700;
  color: #111827;
  margin: 0;
}

.barra-ferramentas {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}

.campo-busca {
  flex: 1;
  min-width: 240px;
  max-width: 420px;
  padding: 10px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 1rem;
  background-color: #ffffff;
  transition:
    border-color 0.2s,
    box-shadow 0.2s;
}

.campo-busca:focus,
.seletor-filtro:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.seletor-filtro {
  padding: 10px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 0.95rem;
  color: #111827;
  background-color: #ffffff;
}

.estado {
  padding: 24px;
  color: #4b5563;
  background-color: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
}

.aviso-erro {
  padding: 16px;
  color: #b91c1c;
  background-color: #fef2f2;
  border: 1px solid #fecaca;
  border-radius: 8px;
}

.tabela-card {
  background-color: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
  overflow: hidden;
  transition: opacity 0.15s;
}

.tabela-card.atualizando {
  opacity: 0.6;
}

.contagem {
  margin: 0;
  padding: 16px 24px;
  font-size: 0.9rem;
  color: #4b5563;
}

.tabela {
  width: 100%;
  border-collapse: collapse;
}

.tabela th {
  text-align: left;
  padding: 12px 24px;
  font-size: 0.85rem;
  font-weight: 600;
  color: #374151;
  background-color: #f9fafb;
  border-bottom: 1px solid #e5e7eb;
}

.tabela td {
  padding: 12px 24px;
  font-size: 0.95rem;
  color: #111827;
  border-bottom: 1px solid #e5e7eb;
}

.tabela tbody tr:last-child td {
  border-bottom: none;
}

.botao-ordenar {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 0;
  border: none;
  background: none;
  font: inherit;
  color: inherit;
  cursor: pointer;
}

.botao-ordenar:hover {
  color: #111827;
}

.botao-ordenar:focus-visible {
  outline: 2px solid #3b82f6;
  outline-offset: 2px;
  border-radius: 4px;
}

.indicador {
  font-size: 0.7rem;
  min-width: 10px;
}

.celula-nome {
  display: flex;
  align-items: center;
  gap: 12px;
}

.avatar {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  flex-shrink: 0;
  border-radius: 9999px;
  background-color: #dbeafe;
  color: #1e40af;
  font-size: 0.8rem;
  font-weight: 600;
}

.selo-bolsista {
  padding: 2px 8px;
  border-radius: 9999px;
  border: 1px solid #99f6e4;
  background-color: #f0fdfa;
  color: #115e59;
  font-size: 0.75rem;
  font-weight: 500;
}

.badge {
  display: inline-block;
  padding: 4px 10px;
  border-radius: 9999px;
  font-size: 0.75rem;
  font-weight: 600;
  white-space: nowrap;
}

.status-ativo {
  background-color: #ecfdf5;
  color: #065f46;
}

.status-trancado {
  background-color: #fffbeb;
  color: #92400e;
}

.status-desligamento {
  background-color: #fef2f2;
  color: #b91c1c;
}

.status-desligado {
  background-color: #f3f4f6;
  color: #4b5563;
}

.status-pos-defesa {
  background-color: #eff6ff;
  color: #1e40af;
}

.status-titulado {
  background-color: #f5f3ff;
  color: #5b21b6;
}

.paginacao {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 16px 24px;
  border-top: 1px solid #e5e7eb;
}

.paginacao-info,
.paginacao-pagina,
.por-pagina {
  font-size: 0.9rem;
  color: #4b5563;
}

.paginacao-controles {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 12px;
}

.por-pagina {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}

.seletor {
  padding: 6px 8px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 0.9rem;
  background-color: #ffffff;
}

.seletor:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}
</style>
