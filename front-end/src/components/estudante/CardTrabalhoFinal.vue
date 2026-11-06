<script setup>
import { ref, computed, watch } from 'vue'
import BaseButton from '../BaseButton.vue'
import BaseModal from '../BaseModal.vue'
import ModalQualificacao from './ModalQualificacao.vue'
import ModalDefesa from './ModalDefesa.vue'
import { useAuthStore } from '../../stores/auth'

const props = defineProps({
  idEstudante: { type: Number, required: true },
})

const emit = defineEmits(['aviso'])

const api = 'http://localhost:8000'
const authStore = useAuthStore()

// Valores iguais aos do backend (back-end/db/enumStatus.py).
const opcoesStatusDissertacao = [
  { valor: 'EM ANDAMENTO', rotulo: 'Em andamento', classe: 'situacao-submetida' },
  { valor: 'CONCLUÍDA', rotulo: 'Concluída', classe: 'situacao-aprovada' },
  { valor: 'CANCELADA', rotulo: 'Cancelada', classe: 'situacao-cancelada' },
]
const opcoesStatusQualificacao = [
  { valor: 'PENDENTE', rotulo: 'Pendente', classe: 'situacao-pendente' },
  { valor: 'ENTREGUE', rotulo: 'Entregue', classe: 'situacao-aprovada' },
  { valor: 'DISPENSA', rotulo: 'Dispensa', classe: 'situacao-dispensa' },
  { valor: 'REPROVADO', rotulo: 'Reprovado', classe: 'situacao-cancelada' },
]
const opcoesStatusDefesa = [
  { valor: 'PENDENTE', rotulo: 'Pendente', classe: 'situacao-pendente' },
  { valor: 'Em homologação', rotulo: 'Em homologação', classe: 'situacao-submetida' },
  { valor: 'Defendida', rotulo: 'Defendida', classe: 'situacao-aprovada' },
  { valor: 'Concluído', rotulo: 'Concluído', classe: 'situacao-aprovada' },
  { valor: 'CANCELADO', rotulo: 'Cancelado', classe: 'situacao-cancelada' },
]
const opcoesConceito = [
  { valor: 'APROVADO', rotulo: 'Aprovado', classe: 'situacao-aprovada' },
  {
    valor: 'APROVADO_CONDICIONALMENTE',
    rotulo: 'Aprovado condicionalmente',
    classe: 'situacao-pendente',
  },
  { valor: 'REPROVADO', rotulo: 'Reprovado', classe: 'situacao-cancelada' },
]
const opcoesHomologacao = [
  { valor: 'PENDENTE', rotulo: 'Pendente', classe: 'situacao-pendente' },
  { valor: 'SOLICITADA', rotulo: 'Solicitada', classe: 'situacao-submetida' },
  { valor: 'APROVADA_COLEGIADO', rotulo: 'Aprovada pelo colegiado', classe: 'situacao-aprovada' },
]

const dissertacao = ref(null)
const qualificacoes = ref([])
const defesas = ref([])
const carregando = ref(false)
const erroBuscaDissertacao = ref('')
const erroBuscaQualificacao = ref('')
const erroBuscaDefesa = ref('')

// Modal da dissertação
const modalDissertacaoAberto = ref(false)
const salvandoDissertacao = ref(false)
const erroFormDissertacao = ref('')
const formDissertacao = ref({})

// Modal da qualificação
const modalQualificacaoAberto = ref(false)
const modalDefesaAberto = ref(false)

const qualificacaoAtual = computed(() => maisRecente(qualificacoes.value, 'id_qualificacao'))
const defesaAtual = computed(() => maisRecente(defesas.value, 'id_defesa'))

// O id da dissertação também vem na qualificação e na defesa:
// assim conseguimos descobri-lo mesmo se a busca da dissertação falhar.
const idDissertacao = computed(
  () =>
    dissertacao.value?.id_dissertacao ??
    qualificacaoAtual.value?.id_dissertacao ??
    defesaAtual.value?.id_dissertacao ??
    null,
)

function maisRecente(lista, campoId) {
  if (!lista || lista.length === 0) return null
  return [...lista].sort((a, b) => b[campoId] - a[campoId])[0]
}

function paraLista(dados) {
  if (Array.isArray(dados)) return dados
  return dados ? [dados] : []
}

function cabecalho() {
  return { Authorization: `Bearer ${authStore.token}` }
}

function formatarData(texto) {
  if (!texto) return '—'
  const [ano, mes, dia] = texto.slice(0, 10).split('-')
  if (!ano || !mes || !dia) return texto
  return `${dia}/${mes}/${ano}`
}

function dataDeHoje() {
  const agora = new Date()
  const mes = String(agora.getMonth() + 1).padStart(2, '0')
  const dia = String(agora.getDate()).padStart(2, '0')
  return `${agora.getFullYear()}-${mes}-${dia}`
}

function situacao(opcoes, valor) {
  return (
    opcoes.find((o) => o.valor === valor) || {
      rotulo: valor || '—',
      classe: 'situacao-dispensa',
    }
  )
}

async function lerMensagemDeErro(resposta) {
  try {
    const dados = await resposta.json()
    if (typeof dados.detail === 'string') return dados.detail
  } catch {
    // A resposta não veio em JSON.
  }
  return ''
}

async function buscarPorAluno(caminho) {
  const resposta = await fetch(`${api}${caminho}/aluno/${props.idEstudante}`, {
    headers: cabecalho(),
  })
  if (resposta.status === 404) return []
  if (!resposta.ok) throw new Error(`${caminho} ${resposta.status}`)
  return paraLista(await resposta.json())
}

async function buscarTudo() {
  carregando.value = true
  erroBuscaDissertacao.value = ''
  erroBuscaQualificacao.value = ''
  erroBuscaDefesa.value = ''

  // allSettled: espera as três buscas e mostra o que deu certo, mesmo se uma falhar.
  const [resDissertacoes, resQualificacoes, resDefesas] = await Promise.allSettled([
    buscarPorAluno('/dissertacoes'),
    buscarPorAluno('/qualificacoes'),
    buscarPorAluno('/defesas'),
  ])

  if (resDissertacoes.status === 'fulfilled') {
    dissertacao.value = maisRecente(resDissertacoes.value, 'id_dissertacao')
  } else {
    dissertacao.value = null
    erroBuscaDissertacao.value = 'Não foi possível carregar a dissertação.'
  }

  if (resQualificacoes.status === 'fulfilled') {
    qualificacoes.value = resQualificacoes.value
  } else {
    qualificacoes.value = []
    erroBuscaQualificacao.value = 'Não foi possível carregar a qualificação.'
  }

  if (resDefesas.status === 'fulfilled') {
    defesas.value = resDefesas.value
  } else {
    defesas.value = []
    erroBuscaDefesa.value = 'Não foi possível carregar a defesa.'
  }

  carregando.value = false
}

// ---------- Modal: Dissertação ----------

function abrirModalDissertacao() {
  formDissertacao.value = dissertacao.value
    ? {
        titulo: dissertacao.value.titulo || '',
        data_inicio: (dissertacao.value.data_inicio || '').slice(0, 10),
        status_dissertacao: dissertacao.value.status_dissertacao || 'EM ANDAMENTO',
      }
    : {
        titulo: '',
        data_inicio: dataDeHoje(),
        status_dissertacao: 'EM ANDAMENTO',
      }
  erroFormDissertacao.value = ''
  modalDissertacaoAberto.value = true
}

function fecharModalDissertacao() {
  if (salvandoDissertacao.value) return
  modalDissertacaoAberto.value = false
}

async function salvarDissertacao() {
  const titulo = formDissertacao.value.titulo.trim()
  if (!titulo) {
    erroFormDissertacao.value = 'Informe o título da dissertação.'
    return
  }
  const editando = dissertacao.value !== null
  if (!editando && !formDissertacao.value.data_inicio) {
    erroFormDissertacao.value = 'Informe a data de início.'
    return
  }

  // O PUT do backend não aceita data_inicio: ao editar, mandamos só título e status.
  const dados = editando
    ? { titulo, status_dissertacao: formDissertacao.value.status_dissertacao }
    : {
        id_estudante: props.idEstudante,
        titulo,
        data_inicio: formDissertacao.value.data_inicio,
        status_dissertacao: formDissertacao.value.status_dissertacao,
      }
  const url = editando
    ? `${api}/dissertacoes/${dissertacao.value.id_dissertacao}`
    : `${api}/dissertacoes`

  erroFormDissertacao.value = ''
  salvandoDissertacao.value = true
  try {
    const resposta = await fetch(url, {
      method: editando ? 'PUT' : 'POST',
      headers: { ...cabecalho(), 'Content-Type': 'application/json' },
      body: JSON.stringify(dados),
    })

    if (!resposta.ok) {
      const detalhe = await lerMensagemDeErro(resposta)
      if (resposta.status === 401) {
        erroFormDissertacao.value = 'Sua sessão expirou. Saia e entre de novo.'
      } else if (resposta.status === 403) {
        erroFormDissertacao.value = 'Você não tem permissão para registrar dissertações.'
      } else {
        erroFormDissertacao.value = detalhe || 'Não foi possível salvar. Confira os dados.'
      }
      return
    }

    if (editando) {
      try {
        const salva = await resposta.json()
        if (salva && salva.id_dissertacao) dissertacao.value = salva
      } catch {
        buscarTudo()
      }
    } else {
      buscarTudo()
    }

    modalDissertacaoAberto.value = false
    emit('aviso', editando ? 'Dissertação atualizada.' : 'Dissertação registrada.', 'sucesso')
  } catch {
    erroFormDissertacao.value = 'Não foi possível conectar ao servidor.'
  } finally {
    salvandoDissertacao.value = false
  }
}

// ---------- Modal: Qualificação ----------

function aoSalvarQualificacao(salva, editando) {
  if (salva && salva.id_qualificacao) {
    qualificacoes.value = editando
      ? qualificacoes.value.map((q) => (q.id_qualificacao === salva.id_qualificacao ? salva : q))
      : [...qualificacoes.value, salva]
  } else {
    buscarTudo()
  }
  modalQualificacaoAberto.value = false
  emit('aviso', editando ? 'Qualificação atualizada.' : 'Qualificação registrada.', 'sucesso')
}

function aoSalvarDefesa(salva, editando) {
  if (salva && salva.id_defesa) {
    defesas.value = editando
      ? defesas.value.map((d) => (d.id_defesa === salva.id_defesa ? salva : d))
      : [...defesas.value, salva]
  } else {
    buscarTudo()
  }
  modalDefesaAberto.value = false
  emit('aviso', editando ? 'Defesa atualizada.' : 'Defesa registrada.', 'sucesso')
}

watch(() => props.idEstudante, buscarTudo, { immediate: true })
</script>

<template>
  <section class="card">
    <div class="card-topo">
      <h2>Dissertação, qualificação e defesa</h2>
    </div>

    <p v-if="carregando" class="texto-vazio">Carregando...</p>
    <div v-else class="marcos-grid">
      <!-- Dissertação -->
      <div class="marco">
        <div class="marco-topo">
          <h3>Dissertação</h3>
          <button
            v-if="!erroBuscaDissertacao"
            type="button"
            class="botao-tabela"
            @click="abrirModalDissertacao"
          >
            {{ dissertacao ? 'Editar' : 'Registrar' }}
          </button>
        </div>
        <p v-if="erroBuscaDissertacao" class="aviso-erro">{{ erroBuscaDissertacao }}</p>
        <dl v-else-if="dissertacao" class="marco-dados">
          <div class="dado-largo">
            <dt>Título</dt>
            <dd v-if="dissertacao.titulo">{{ dissertacao.titulo }}</dd>
            <dd v-else class="texto-vazio">Sem título</dd>
          </div>
          <div>
            <dt>Início</dt>
            <dd>{{ formatarData(dissertacao.data_inicio) }}</dd>
          </div>
          <div>
            <dt>Status</dt>
            <dd>
              <span
                class="badge"
                :class="situacao(opcoesStatusDissertacao, dissertacao.status_dissertacao).classe"
              >
                {{ situacao(opcoesStatusDissertacao, dissertacao.status_dissertacao).rotulo }}
              </span>
            </dd>
          </div>
        </dl>
        <p v-else class="texto-vazio">Nenhuma dissertação registrada.</p>
      </div>

      <!-- Qualificação -->
      <div class="marco">
        <div class="marco-topo">
          <h3>Qualificação</h3>
          <button
            v-if="!erroBuscaQualificacao"
            type="button"
            class="botao-tabela"
            :disabled="!qualificacaoAtual && !idDissertacao"
            @click="modalQualificacaoAberto = true"
          >
            {{ qualificacaoAtual ? 'Atualizar' : 'Registrar' }}
          </button>
        </div>
        <p v-if="erroBuscaQualificacao" class="aviso-erro">{{ erroBuscaQualificacao }}</p>
        <dl v-else-if="qualificacaoAtual" class="marco-dados">
          <div>
            <dt>Status</dt>
            <dd>
              <span
                class="badge"
                :class="
                  situacao(opcoesStatusQualificacao, qualificacaoAtual.status_qualificacao).classe
                "
              >
                {{
                  situacao(opcoesStatusQualificacao, qualificacaoAtual.status_qualificacao).rotulo
                }}
              </span>
            </dd>
          </div>
          <div>
            <dt>Tentativa</dt>
            <dd>{{ qualificacaoAtual.tentativa ?? '—' }}</dd>
          </div>
          <div>
            <dt>Prazo máximo</dt>
            <dd>{{ formatarData(qualificacaoAtual.prazo_maximo_qualificacao) }}</dd>
          </div>
          <div>
            <dt>Realização</dt>
            <dd>{{ formatarData(qualificacaoAtual.data_realizacao) }}</dd>
          </div>
          <div>
            <dt>Retorno</dt>
            <dd>{{ qualificacaoAtual.retorno_qualificacao || '—' }}</dd>
          </div>
        </dl>
        <p v-else-if="!idDissertacao" class="texto-vazio">Registre a dissertação primeiro.</p>
        <p v-else class="texto-vazio">Nenhuma qualificação registrada.</p>
      </div>

      <!-- Defesa -->
      <div class="marco">
        <div class="marco-topo">
          <h3>Defesa</h3>
          <button
            v-if="!erroBuscaDefesa"
            type="button"
            class="botao-tabela"
            :disabled="!defesaAtual && !idDissertacao"
            @click="modalDefesaAberto = true"
          >
            {{ defesaAtual ? 'Atualizar' : 'Registrar' }}
          </button>
        </div>
        <p v-if="erroBuscaDefesa" class="aviso-erro">{{ erroBuscaDefesa }}</p>
        <dl v-else-if="defesaAtual" class="marco-dados">
          <div>
            <dt>Status</dt>
            <dd>
              <span
                class="badge"
                :class="situacao(opcoesStatusDefesa, defesaAtual.status_defesa).classe"
              >
                {{ situacao(opcoesStatusDefesa, defesaAtual.status_defesa).rotulo }}
              </span>
            </dd>
          </div>
          <div>
            <dt>Homologação da banca</dt>
            <dd>
              <span
                class="badge"
                :class="situacao(opcoesHomologacao, defesaAtual.status_homologacao_banca).classe"
              >
                {{ situacao(opcoesHomologacao, defesaAtual.status_homologacao_banca).rotulo }}
              </span>
            </dd>
          </div>
          <div>
            <dt>Prazo máximo</dt>
            <dd>{{ formatarData(defesaAtual.prazo_maximo_defesa) }}</dd>
          </div>
          <div>
            <dt>Realização</dt>
            <dd>{{ formatarData(defesaAtual.data_realizacao) }}</dd>
          </div>
          <div>
            <dt>Conceito</dt>
            <dd>
              <span
                v-if="defesaAtual.conceito_defesa"
                class="badge"
                :class="situacao(opcoesConceito, defesaAtual.conceito_defesa).classe"
              >
                {{ situacao(opcoesConceito, defesaAtual.conceito_defesa).rotulo }}
              </span>
              <span v-else>—</span>
            </dd>
          </div>
        </dl>
        <p v-else-if="!idDissertacao" class="texto-vazio">Registre a dissertação primeiro.</p>
        <p v-else class="texto-vazio">Nenhuma defesa registrada.</p>
      </div>
    </div>

    <BaseModal
      :aberto="modalDissertacaoAberto"
      :titulo="dissertacao ? 'Editar dissertação' : 'Registrar dissertação'"
      @fechar="fecharModalDissertacao"
    >
      <form id="form-dissertacao" class="form-grid" @submit.prevent="salvarDissertacao">
        <div class="form-group span-full">
          <label for="dissertacao-titulo">Título *</label>
          <input
            id="dissertacao-titulo"
            v-model="formDissertacao.titulo"
            type="text"
            maxlength="255"
            required
          />
        </div>

        <div class="form-group">
          <label for="dissertacao-inicio">Data de início *</label>
          <input
            id="dissertacao-inicio"
            v-model="formDissertacao.data_inicio"
            type="date"
            :required="!dissertacao"
            :disabled="Boolean(dissertacao)"
          />
        </div>

        <div class="form-group">
          <label for="dissertacao-status">Status *</label>
          <select id="dissertacao-status" v-model="formDissertacao.status_dissertacao" required>
            <option v-for="o in opcoesStatusDissertacao" :key="o.valor" :value="o.valor">
              {{ o.rotulo }}
            </option>
          </select>
        </div>

        <p v-if="dissertacao" class="dica span-full">
          A data de início não pode ser alterada depois do cadastro.
        </p>

        <p v-if="erroFormDissertacao" class="aviso-erro span-full">{{ erroFormDissertacao }}</p>
      </form>

      <template #rodape>
        <BaseButton
          type="button"
          variant="secondary"
          :disabled="salvandoDissertacao"
          @click="fecharModalDissertacao"
        >
          Cancelar
        </BaseButton>
        <BaseButton
          type="submit"
          form="form-dissertacao"
          variant="primary"
          :disabled="salvandoDissertacao"
        >
          {{ salvandoDissertacao ? 'Salvando...' : 'Salvar' }}
        </BaseButton>
      </template>
    </BaseModal>

    <ModalQualificacao
      :aberto="modalQualificacaoAberto"
      :qualificacao="qualificacaoAtual"
      :id-dissertacao="idDissertacao"
      @fechar="modalQualificacaoAberto = false"
      @salvo="aoSalvarQualificacao"
    />
    <ModalDefesa
      :aberto="modalDefesaAberto"
      :defesa="defesaAtual"
      :id-dissertacao="idDissertacao"
      @fechar="modalDefesaAberto = false"
      @salvo="aoSalvarDefesa"
    />
  </section>
</template>

<style scoped>
.card {
  margin-bottom: 24px;
  padding: 24px;
  background-color: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
}

.card-topo {
  margin-bottom: 16px;
  padding-bottom: 8px;
  border-bottom: 1px solid #e5e7eb;
}

.card-topo h2 {
  margin: 0;
  font-size: 1.25rem;
  color: #374151;
}

.texto-vazio {
  margin: 0;
  color: #9ca3af;
  font-style: italic;
}

.aviso-erro {
  margin: 0;
  padding: 12px 16px;
  color: #b91c1c;
  background-color: #fef2f2;
  border: 1px solid #fecaca;
  border-radius: 8px;
  font-size: 0.9rem;
}

.marcos-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 16px;
}

.marco {
  padding: 16px;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  background-color: #f9fafb;
}

.marco-topo {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 12px;
}

.marco-topo h3 {
  margin: 0;
  font-size: 1rem;
  color: #374151;
}

.marco-dados {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(170px, 1fr));
  gap: 12px 24px;
  margin: 0;
}

.marco-dados .dado-largo {
  grid-column: 1 / -1;
}

.marco-dados dt {
  margin-bottom: 2px;
  font-size: 0.8rem;
  font-weight: 500;
  color: #6b7280;
}

.marco-dados dd {
  margin: 0;
  font-size: 0.95rem;
  color: #111827;
  overflow-wrap: anywhere;
}

.botao-tabela {
  padding: 4px 10px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  background-color: #ffffff;
  color: #374151;
  font: inherit;
  font-size: 0.8rem;
  cursor: pointer;
}

.botao-tabela:hover:not(:disabled) {
  background-color: #f9fafb;
  border-color: #9ca3af;
}

.botao-tabela:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.botao-tabela:focus-visible {
  outline: 2px solid #3b82f6;
  outline-offset: 2px;
}

.badge {
  display: inline-block;
  padding: 4px 10px;
  border-radius: 9999px;
  font-size: 0.75rem;
  font-weight: 600;
  white-space: nowrap;
}

.situacao-aprovada {
  background-color: #ecfdf5;
  color: #065f46;
}

.situacao-submetida {
  background-color: #eff6ff;
  color: #1e40af;
}

.situacao-pendente {
  background-color: #fffbeb;
  color: #92400e;
}

.situacao-dispensa {
  background-color: #f3f4f6;
  color: #4b5563;
}

.situacao-cancelada {
  background-color: #fef2f2;
  color: #b91c1c;
}

.form-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.span-full {
  grid-column: 1 / -1;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.form-group label {
  font-size: 0.875rem;
  font-weight: 500;
  color: #374151;
}

.form-group input,
.form-group select {
  padding: 10px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 0.95rem;
  font-family: inherit;
}

.form-group input:disabled {
  background-color: #f3f4f6;
  color: #6b7280;
}

.form-group input:focus,
.form-group select:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.dica {
  margin: 0;
  font-size: 0.8rem;
  color: #6b7280;
}
</style>
