<script setup>
import { ref, computed, watch, onMounted, onBeforeUnmount } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import DefaultLayout from '../layouts/DefaultLayout.vue'
import BaseButton from '../components/BaseButton.vue'
import { useAuthStore } from '../stores/auth'

const authStore = useAuthStore()
const route = useRoute()
const router = useRouter()

const estudantes = ref([])
const total = ref(0)
const carregando = ref(false)
const erro = ref('')

const colunasOrdenaveis = ['nome_discente', 'matricula', 'id_semestre']
const colunaPadrao = 'nome_discente'
const colunaOrdenacao = ref(colunaPadrao)
const ordemDesc = ref(false)

const opcoesPorPagina = [10, 25, 50]
const porPaginaPadrao = 10
const porPagina = ref(porPaginaPadrao)
const paginaAtual = ref(1)

const termoBusca = ref('')
let temporizadorBusca = null
let ultimaRequisicao = 0
let ultimaBuscaEnviada = ''
let ultimaQueryEscrita = ''

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
const filtroOrientador = ref('')
const filtroBolsa = ref('')

const semestres = ref([])
const professores = ref([])

const diasParaAvisoPrazo = 180
const statusSemAvisoPrazo = ['TITULADO', 'DESLIGADO']

const chaveVisaoCompacta = 'estudantes_visao_compacta'
const visaoCompacta = ref(lerVisaoCompacta())

const aviso = ref(null)
let temporizadorAviso = null

const totalPaginas = computed(() => Math.max(1, Math.ceil(total.value / porPagina.value)))
const inicioIntervalo = computed(() =>
  total.value === 0 ? 0 : (paginaAtual.value - 1) * porPagina.value + 1,
)
const fimIntervalo = computed(
  () => (paginaAtual.value - 1) * porPagina.value + estudantes.value.length,
)
const termoBuscaLimpo = computed(() => termoBusca.value.trim())
const temFiltroAtivo = computed(
  () =>
    filtroStatus.value !== '' ||
    filtroSemestre.value !== '' ||
    filtroOrientador.value !== '' ||
    filtroBolsa.value !== '',
)
const codigosSemestres = computed(() => {
  const mapa = {}
  for (const semestre of semestres.value) {
    mapa[semestre.id_semestre] = semestre.codigo_semestre
  }
  return mapa
})
const nomesProfessores = computed(() => {
  const mapa = {}
  for (const professor of professores.value) {
    mapa[professor.id_professor] = professor.nome_professor
  }
  return mapa
})
const professoresOrdenados = computed(() =>
  [...professores.value].sort((a, b) => a.nome_professor.localeCompare(b.nome_professor, 'pt-BR')),
)
const linhas = computed(() =>
  estudantes.value.map((estudante) => ({
    ...estudante,
    avisoPrazo: avisoDoPrazo(estudante),
  })),
)

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

function nomeDoOrientador(idOrientador) {
  return nomesProfessores.value[idOrientador] || `Professor ${idOrientador}`
}

function iniciais(nome) {
  const partes = (nome || '').trim().split(/\s+/).filter(Boolean)
  if (partes.length === 0) return '?'
  const primeira = partes[0][0]
  const ultima = partes.length > 1 ? partes[partes.length - 1][0] : ''
  return (primeira + ultima).toUpperCase()
}

// ---------- Prazo ----------

function formatarData(texto) {
  if (!texto) return '—'
  const [ano, mes, dia] = texto.slice(0, 10).split('-')
  if (!ano || !mes || !dia) return texto
  return `${dia}/${mes}/${ano}`
}

function diasAtePrazo(texto) {
  if (!texto) return null
  const [ano, mes, dia] = texto.slice(0, 10).split('-').map(Number)
  if (!ano || !mes || !dia) return null
  const prazo = new Date(ano, mes - 1, dia)
  const agora = new Date()
  const hoje = new Date(agora.getFullYear(), agora.getMonth(), agora.getDate())
  return Math.round((prazo - hoje) / (1000 * 60 * 60 * 24))
}

function textoDias(quantidade) {
  return quantidade === 1 ? '1 dia' : `${quantidade} dias`
}

function avisoDoPrazo(estudante) {
  if (statusSemAvisoPrazo.includes(estudante.status_atual)) return null
  const dias = diasAtePrazo(estudante.prazo_conclusao_sigaa)
  if (dias === null) return null
  if (dias < 0) {
    return { classe: 'prazo-vencido', texto: `Prazo vencido há ${textoDias(-dias)}` }
  }
  if (dias === 0) {
    return { classe: 'prazo-proximo', texto: 'O prazo termina hoje' }
  }
  if (dias <= diasParaAvisoPrazo) {
    return { classe: 'prazo-proximo', texto: `Faltam ${textoDias(dias)} para o prazo` }
  }
  return null
}

// ---------- Aviso flutuante ----------

function mostrarAviso(texto, tipo) {
  aviso.value = { texto, tipo }
  clearTimeout(temporizadorAviso)
  temporizadorAviso = setTimeout(() => {
    aviso.value = null
  }, 3000)
}

// ---------- Ações por linha ----------

async function copiarTexto(texto, mensagemSucesso, mensagemErro) {
  try {
    await navigator.clipboard.writeText(texto)
    mostrarAviso(mensagemSucesso, 'sucesso')
  } catch {
    mostrarAviso(mensagemErro, 'erro')
  }
}

function copiarEmail(estudante) {
  copiarTexto(estudante.email, 'E-mail copiado!', 'Não foi possível copiar o e-mail.')
}

function copiarMatricula(estudante) {
  copiarTexto(estudante.matricula, 'Matrícula copiada!', 'Não foi possível copiar a matrícula.')
}

// ---------- Visão compacta ----------

function lerVisaoCompacta() {
  try {
    return localStorage.getItem(chaveVisaoCompacta) === 'true'
  } catch {
    return false
  }
}

function alternarVisaoCompacta() {
  visaoCompacta.value = !visaoCompacta.value
  try {
    localStorage.setItem(chaveVisaoCompacta, String(visaoCompacta.value))
  } catch {
    // Se o navegador não deixar salvar, a escolha vale só até recarregar.
  }
}

// ---------- URL (query params) ----------

function lerTexto(valor) {
  const primeiro = Array.isArray(valor) ? valor[0] : valor
  return typeof primeiro === 'string' ? primeiro : ''
}

function lerInteiroPositivo(valor) {
  const texto = lerTexto(valor)
  if (!/^\d+$/.test(texto)) return null
  const numero = Number(texto)
  return numero >= 1 ? numero : null
}

function lerEstadoDaUrl() {
  const query = route.query

  termoBusca.value = lerTexto(query.busca).slice(0, 100)

  const status = lerTexto(query.status)
  filtroStatus.value = opcoesStatus.includes(status) ? status : ''

  const semestre = lerInteiroPositivo(query.semestre)
  filtroSemestre.value = semestre === null ? '' : semestre

  const orientador = lerInteiroPositivo(query.orientador)
  filtroOrientador.value = orientador === null ? '' : orientador

  const bolsa = lerTexto(query.bolsa)
  filtroBolsa.value = bolsa === 'true' || bolsa === 'false' ? bolsa : ''

  const quantidade = lerInteiroPositivo(query.por_pagina)
  porPagina.value = opcoesPorPagina.includes(quantidade) ? quantidade : porPaginaPadrao

  paginaAtual.value = lerInteiroPositivo(query.pagina) || 1

  const coluna = lerTexto(query.ordenar)
  colunaOrdenacao.value = colunasOrdenaveis.includes(coluna) ? coluna : colunaPadrao

  ordemDesc.value = lerTexto(query.desc) === 'true'
}

function montarQuery() {
  const query = {}
  if (termoBuscaLimpo.value) query.busca = termoBuscaLimpo.value
  if (filtroStatus.value !== '') query.status = filtroStatus.value
  if (filtroSemestre.value !== '') query.semestre = String(filtroSemestre.value)
  if (filtroOrientador.value !== '') query.orientador = String(filtroOrientador.value)
  if (filtroBolsa.value !== '') query.bolsa = filtroBolsa.value
  if (paginaAtual.value !== 1) query.pagina = String(paginaAtual.value)
  if (porPagina.value !== porPaginaPadrao) query.por_pagina = String(porPagina.value)
  if (colunaOrdenacao.value !== colunaPadrao) query.ordenar = colunaOrdenacao.value
  if (ordemDesc.value) query.desc = 'true'
  return query
}

function atualizarUrl() {
  const query = montarQuery()
  ultimaQueryEscrita = JSON.stringify(query)
  if (ultimaQueryEscrita !== JSON.stringify(route.query)) {
    router.replace({ query })
  }
}

// ---------- Ações da tela ----------

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
  filtroOrientador.value = ''
  filtroBolsa.value = ''
  aplicarFiltros()
}

watch(termoBusca, () => {
  clearTimeout(temporizadorBusca)
  temporizadorBusca = setTimeout(() => {
    if (termoBuscaLimpo.value === ultimaBuscaEnviada) return
    paginaAtual.value = 1
    buscarEstudantes()
  }, 400)
})

watch(
  () => route.query,
  (novaQuery) => {
    if (route.name !== 'estudantes') return
    if (JSON.stringify(novaQuery) === ultimaQueryEscrita) return
    lerEstadoDaUrl()
    buscarEstudantes()
  },
)

// ---------- Pedidos à API ----------

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

async function buscarProfessores() {
  try {
    const resposta = await fetch('http://localhost:8000/professores?limit=200', {
      headers: { Authorization: `Bearer ${authStore.token}` },
    })
    if (!resposta.ok) return
    professores.value = await resposta.json()
  } catch {
    // Sem a lista de professores, a tabela mostra "Professor" e o número.
  }
}

async function buscarEstudantes() {
  const numeroRequisicao = ++ultimaRequisicao
  ultimaBuscaEnviada = termoBuscaLimpo.value
  atualizarUrl()
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
  if (filtroOrientador.value !== '') {
    parametros.set('id_orientador', String(filtroOrientador.value))
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
    if (dados.itens.length === 0 && dados.total > 0 && paginaAtual.value > 1) {
      paginaAtual.value = Math.max(1, Math.ceil(dados.total / porPagina.value))
      buscarEstudantes()
      return
    }
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

lerEstadoDaUrl()

onMounted(() => {
  buscarSemestres()
  buscarProfessores()
  buscarEstudantes()
})

onBeforeUnmount(() => {
  clearTimeout(temporizadorBusca)
  clearTimeout(temporizadorAviso)
})
</script>

<template>
  <DefaultLayout>
    <div
      v-if="aviso"
      class="aviso-flutuante"
      :class="aviso.tipo === 'erro' ? 'aviso-flutuante-erro' : 'aviso-flutuante-sucesso'"
      role="status"
    >
      {{ aviso.texto }}
    </div>

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
        v-model="filtroOrientador"
        class="seletor-filtro"
        aria-label="Filtrar por orientador"
        @change="aplicarFiltros"
      >
        <option value="">Todos os orientadores</option>
        <option
          v-for="professor in professoresOrdenados"
          :key="professor.id_professor"
          :value="professor.id_professor"
        >
          {{ professor.nome_professor }}
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
      <div class="cabecalho-tabela">
        <p class="contagem">
          {{ total }} {{ total === 1 ? 'estudante encontrado' : 'estudantes encontrados' }}
        </p>
        <button
          type="button"
          class="botao-compacta"
          :class="{ ativo: visaoCompacta }"
          :aria-pressed="visaoCompacta"
          @click="alternarVisaoCompacta"
        >
          Visão compacta
        </button>
      </div>

      <div class="tabela-rolagem">
        <table class="tabela" :class="{ compacta: visaoCompacta }">
          <thead>
            <tr>
              <th>
                <button type="button" class="botao-ordenar" @click="ordenarPor('nome_discente')">
                  Estudante
                  <span class="indicador">{{ indicadorOrdenacao('nome_discente') }}</span>
                </button>
              </th>
              <th>
                <button type="button" class="botao-ordenar" @click="ordenarPor('matricula')">
                  Matrícula <span class="indicador">{{ indicadorOrdenacao('matricula') }}</span>
                </button>
              </th>
              <th>Orientador</th>
              <th>
                <button type="button" class="botao-ordenar" @click="ordenarPor('id_semestre')">
                  Semestre <span class="indicador">{{ indicadorOrdenacao('id_semestre') }}</span>
                </button>
              </th>
              <th>Status</th>
              <th>Prazo (SIGAA)</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="estudante in linhas" :key="estudante.id_estudante">
              <td>
                <div class="celula-estudante">
                  <span class="avatar">{{ iniciais(estudante.nome_discente) }}</span>
                  <div class="info-estudante">
                    <div class="linha-nome">
                      <RouterLink :to="`/estudantes/${estudante.id_estudante}`" class="link-nome">
                        {{ estudante.nome_discente }}
                      </RouterLink>
                      <span v-if="estudante.eh_bolsista" class="selo-bolsista">Bolsista</span>
                    </div>
                    <div class="linha-email">
                      <span class="email-estudante">{{ estudante.email }}</span>
                      <button
                        type="button"
                        class="botao-copiar"
                        title="Copiar e-mail"
                        :aria-label="`Copiar e-mail de ${estudante.nome_discente}`"
                        @click="copiarEmail(estudante)"
                      >
                        <svg
                          viewBox="0 0 24 24"
                          width="14"
                          height="14"
                          fill="none"
                          stroke="currentColor"
                          stroke-width="2"
                          stroke-linecap="round"
                          stroke-linejoin="round"
                          aria-hidden="true"
                        >
                          <rect x="9" y="9" width="11" height="11" rx="2" />
                          <path d="M5 15V6a2 2 0 0 1 2-2h9" />
                        </svg>
                      </button>
                    </div>
                  </div>
                </div>
              </td>
              <td>
                <div class="celula-copiavel">
                  <span>{{ estudante.matricula }}</span>
                  <button
                    type="button"
                    class="botao-copiar"
                    title="Copiar matrícula"
                    :aria-label="`Copiar matrícula de ${estudante.nome_discente}`"
                    @click="copiarMatricula(estudante)"
                  >
                    <svg
                      viewBox="0 0 24 24"
                      width="14"
                      height="14"
                      fill="none"
                      stroke="currentColor"
                      stroke-width="2"
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      aria-hidden="true"
                    >
                      <rect x="9" y="9" width="11" height="11" rx="2" />
                      <path d="M5 15V6a2 2 0 0 1 2-2h9" />
                    </svg>
                  </button>
                </div>
              </td>
              <td>
                <span v-if="estudante.id_orientador">
                  {{ nomeDoOrientador(estudante.id_orientador) }}
                </span>
                <span v-else class="sem-orientador">Sem orientador</span>
              </td>
              <td>{{ codigoDoSemestre(estudante.id_semestre) }}</td>
              <td>
                <span class="badge" :class="classeDoStatus(estudante.status_atual)">
                  {{ estudante.status_atual }}
                </span>
              </td>
              <td>
                <div class="celula-prazo">
                  <span>{{ formatarData(estudante.prazo_conclusao_sigaa) }}</span>
                  <span
                    v-if="estudante.avisoPrazo"
                    class="alerta-prazo"
                    :class="estudante.avisoPrazo.classe"
                    role="img"
                    :title="estudante.avisoPrazo.texto"
                    :aria-label="estudante.avisoPrazo.texto"
                  >
                    !
                  </span>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

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

.aviso-flutuante {
  position: fixed;
  top: 80px;
  right: 24px;
  z-index: 50;
  padding: 12px 16px;
  border-radius: 6px;
  font-size: 0.95rem;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.aviso-flutuante-sucesso {
  background-color: #ecfdf5;
  color: #065f46;
  border: 1px solid #a7f3d0;
}

.aviso-flutuante-erro {
  background-color: #fef2f2;
  color: #b91c1c;
  border: 1px solid #fecaca;
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

.cabecalho-tabela {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 12px 16px;
}

.contagem {
  margin: 0;
  font-size: 0.9rem;
  color: #4b5563;
}

.botao-compacta {
  padding: 6px 12px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  background-color: #ffffff;
  color: #374151;
  font: inherit;
  font-size: 0.85rem;
  cursor: pointer;
}

.botao-compacta:hover {
  background-color: #f9fafb;
}

.botao-compacta.ativo {
  background-color: #eff6ff;
  border-color: #93c5fd;
  color: #1e40af;
}

.botao-compacta:focus-visible,
.botao-copiar:focus-visible,
.link-nome:focus-visible {
  outline: 2px solid #3b82f6;
  outline-offset: 2px;
}

.tabela-rolagem {
  overflow-x: auto;
}

.tabela {
  width: 100%;
  border-collapse: collapse;
}

.tabela th {
  text-align: left;
  padding: 12px 16px;
  font-size: 0.85rem;
  font-weight: 600;
  color: #374151;
  background-color: #f9fafb;
  border-bottom: 1px solid #e5e7eb;
  white-space: nowrap;
}

.tabela td {
  padding: 12px 16px;
  font-size: 0.95rem;
  color: #111827;
  border-bottom: 1px solid #e5e7eb;
  white-space: nowrap;
  vertical-align: middle;
}

.tabela tbody tr:last-child td {
  border-bottom: none;
}

.tabela tbody tr:hover td {
  background-color: #f9fafb;
}

.tabela.compacta th {
  padding: 8px 12px;
}

.tabela.compacta td {
  padding: 6px 12px;
  font-size: 0.875rem;
}

.tabela.compacta .avatar {
  width: 24px;
  height: 24px;
  font-size: 0.65rem;
}

.tabela.compacta .email-estudante {
  font-size: 0.75rem;
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

.celula-estudante {
  display: flex;
  align-items: center;
  gap: 12px;
}

.info-estudante {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.linha-nome,
.linha-email,
.celula-copiavel {
  display: flex;
  align-items: center;
  gap: 6px;
}

.linha-nome {
  gap: 8px;
}

.email-estudante {
  font-size: 0.8rem;
  color: #6b7280;
}

.link-nome {
  color: #1d4ed8;
  font-weight: 500;
  text-decoration: none;
  border-radius: 2px;
}

.link-nome:hover {
  text-decoration: underline;
}

.botao-copiar {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  flex-shrink: 0;
  padding: 0;
  border: 1px solid transparent;
  border-radius: 4px;
  background: none;
  color: #9ca3af;
  cursor: pointer;
}

.botao-copiar:hover {
  color: #374151;
  background-color: #f3f4f6;
  border-color: #e5e7eb;
}

.sem-orientador {
  color: #9ca3af;
  font-style: italic;
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

.celula-prazo {
  display: flex;
  align-items: center;
  gap: 8px;
}

.alerta-prazo {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
  flex-shrink: 0;
  border-radius: 9999px;
  font-size: 0.75rem;
  font-weight: 700;
  cursor: help;
}

.prazo-proximo {
  background-color: #fef3c7;
  color: #92400e;
  border: 1px solid #fcd34d;
}

.prazo-vencido {
  background-color: #fee2e2;
  color: #b91c1c;
  border: 1px solid #fca5a5;
}

.paginacao {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 16px;
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
