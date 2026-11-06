<script setup>
import { ref, computed, watch } from 'vue'
import BaseButton from '../BaseButton.vue'
import BaseModal from '../BaseModal.vue'
import { useAuthStore } from '../../stores/auth'

const props = defineProps({
  idEstudante: { type: Number, required: true },
})

const emit = defineEmits(['aviso'])

const api = 'http://localhost:8000'
const authStore = useAuthStore()

// Valores iguais aos do backend (back-end/db/enumStatus.py).
const opcoesTipo = [
  { valor: 'PERIÓDICO', rotulo: 'Periódico' },
  { valor: 'EVENTO', rotulo: 'Evento' },
]
const opcoesQualis = ['A1', 'A2', 'A3', 'A4', 'B1', 'B2']
const opcoesComprovante = [
  { valor: 'SUBMETIDA', rotulo: 'Submetida', classe: 'situacao-submetida' },
  { valor: 'PUBLICADO', rotulo: 'Publicado', classe: 'situacao-aprovada' },
  { valor: 'DISPENSA', rotulo: 'Dispensa', classe: 'situacao-dispensa' },
  { valor: 'NEGADO', rotulo: 'Negado', classe: 'situacao-cancelada' },
]
const opcoesColegiado = [
  { valor: 'PENDENTE', rotulo: 'Pendente', classe: 'situacao-pendente' },
  { valor: 'SUBMETIDA', rotulo: 'Submetida', classe: 'situacao-submetida' },
  { valor: 'APROVADA', rotulo: 'Aprovada', classe: 'situacao-aprovada' },
]

const artigos = ref([])
const carregando = ref(false)
const erro = ref('')

const modalAberto = ref(false)
const salvando = ref(false)
const erroForm = ref('')
const editandoId = ref(null)
const form = ref({})

const artigosOrdenados = computed(() =>
  [...artigos.value].sort((a, b) => b.id_artigo - a.id_artigo),
)

function cabecalho() {
  return { Authorization: `Bearer ${authStore.token}` }
}

function formatarData(texto) {
  if (!texto) return ''
  const [ano, mes, dia] = texto.slice(0, 10).split('-')
  if (!ano || !mes || !dia) return texto
  return `${dia}/${mes}/${ano}`
}

function rotuloTipo(valor) {
  return opcoesTipo.find((t) => t.valor === valor)?.rotulo || valor || '—'
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

async function buscarArtigos() {
  carregando.value = true
  erro.value = ''
  try {
    const resposta = await fetch(`${api}/artigos/estudante/${props.idEstudante}`, {
      headers: cabecalho(),
    })
    if (resposta.status === 404) {
      artigos.value = []
      return
    }
    if (!resposta.ok) {
      erro.value = 'Não foi possível carregar os artigos.'
      return
    }
    const dados = await resposta.json()
    if (Array.isArray(dados)) {
      artigos.value = dados
    } else {
      artigos.value = dados ? [dados] : []
    }
  } catch {
    erro.value = 'Não foi possível carregar os artigos.'
  } finally {
    carregando.value = false
  }
}

function abrirModal(artigo = null) {
  editandoId.value = artigo ? artigo.id_artigo : null
  form.value = artigo
    ? {
        titulo: artigo.titulo || '',
        tipo: artigo.tipo || '',
        qualis: artigo.qualis || '',
        status_comprovante: artigo.status_comprovante || 'SUBMETIDA',
        data_entrega: (artigo.data_entrega || '').slice(0, 10),
        status_validacao_colegiado: artigo.status_validacao_colegiado || 'PENDENTE',
      }
    : {
        titulo: '',
        tipo: '',
        qualis: '',
        status_comprovante: 'SUBMETIDA',
        data_entrega: '',
        status_validacao_colegiado: 'PENDENTE',
      }
  erroForm.value = ''
  modalAberto.value = true
}

function fecharModal() {
  if (salvando.value) return
  modalAberto.value = false
}

function validar() {
  if (!form.value.titulo.trim()) return 'Informe o título do artigo.'
  if (!form.value.tipo) return 'Escolha o tipo do artigo.'
  if (!form.value.status_comprovante) return 'Escolha o status do comprovante.'
  if (!form.value.status_validacao_colegiado) return 'Escolha a validação do colegiado.'
  return ''
}

async function salvar() {
  erroForm.value = validar()
  if (erroForm.value) return

  const editando = editandoId.value !== null
  const dados = {
    id_estudante: props.idEstudante,
    titulo: form.value.titulo.trim(),
    tipo: form.value.tipo,
    qualis: form.value.qualis || null,
    status_comprovante: form.value.status_comprovante,
    data_entrega: form.value.data_entrega || null,
    status_validacao_colegiado: form.value.status_validacao_colegiado,
  }
  const url = editando ? `${api}/artigos/${editandoId.value}` : `${api}/artigos`

  salvando.value = true
  try {
    const resposta = await fetch(url, {
      method: editando ? 'PUT' : 'POST',
      headers: { ...cabecalho(), 'Content-Type': 'application/json' },
      body: JSON.stringify(dados),
    })

    if (!resposta.ok) {
      const detalhe = await lerMensagemDeErro(resposta)
      if (resposta.status === 401) {
        erroForm.value = 'Sua sessão expirou. Saia e entre de novo.'
      } else if (resposta.status === 403) {
        erroForm.value = 'Você não tem permissão para registrar artigos.'
      } else {
        erroForm.value = detalhe || 'Não foi possível salvar. Confira os dados.'
      }
      return
    }

    // Atualiza a tabela na hora com o que a API devolveu.
    let salvo = null
    try {
      salvo = await resposta.json()
    } catch {
      salvo = null
    }
    if (salvo && salvo.id_artigo) {
      artigos.value = editando
        ? artigos.value.map((a) => (a.id_artigo === salvo.id_artigo ? salvo : a))
        : [...artigos.value, salvo]
    } else {
      buscarArtigos()
    }

    modalAberto.value = false
    emit('aviso', editando ? 'Artigo atualizado.' : 'Artigo registrado.', 'sucesso')
  } catch {
    erroForm.value = 'Não foi possível conectar ao servidor.'
  } finally {
    salvando.value = false
  }
}

watch(() => props.idEstudante, buscarArtigos, { immediate: true })
</script>

<template>
  <section class="card">
    <div class="card-topo">
      <h2>Submissão de artigos</h2>
      <BaseButton type="button" variant="secondary" @click="abrirModal()">
        Registrar artigo
      </BaseButton>
    </div>

    <p v-if="carregando" class="texto-vazio">Carregando artigos...</p>
    <p v-else-if="erro" class="aviso-erro">{{ erro }}</p>
    <p v-else-if="artigos.length === 0" class="texto-vazio">Nenhum artigo registrado.</p>
    <div v-else class="tabela-rolagem">
      <table class="tabela-simples">
        <thead>
          <tr>
            <th>Título</th>
            <th>Tipo</th>
            <th>Qualis</th>
            <th>Comprovante</th>
            <th>Colegiado</th>
            <th class="coluna-acoes"><span class="visualmente-oculto">Ações</span></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="artigo in artigosOrdenados" :key="artigo.id_artigo">
            <td class="coluna-titulo">{{ artigo.titulo }}</td>
            <td>{{ rotuloTipo(artigo.tipo) }}</td>
            <td>{{ artigo.qualis || '—' }}</td>
            <td>
              <span
                class="badge"
                :class="situacao(opcoesComprovante, artigo.status_comprovante).classe"
              >
                {{ situacao(opcoesComprovante, artigo.status_comprovante).rotulo }}
              </span>
              <span v-if="artigo.data_entrega" class="data-pequena">
                entregue em {{ formatarData(artigo.data_entrega) }}
              </span>
            </td>
            <td>
              <span
                class="badge"
                :class="situacao(opcoesColegiado, artigo.status_validacao_colegiado).classe"
              >
                {{ situacao(opcoesColegiado, artigo.status_validacao_colegiado).rotulo }}
              </span>
            </td>
            <td class="coluna-acoes">
              <button
                type="button"
                class="botao-tabela"
                :aria-label="`Editar artigo ${artigo.titulo}`"
                @click="abrirModal(artigo)"
              >
                Editar
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <BaseModal
      :aberto="modalAberto"
      :titulo="editandoId ? 'Editar artigo' : 'Registrar artigo'"
      larguraMaxima="680px"
      @fechar="fecharModal"
    >
      <form id="form-artigo" class="form-grid" @submit.prevent="salvar">
        <div class="form-group span-full">
          <label for="artigo-titulo">Título *</label>
          <input id="artigo-titulo" v-model="form.titulo" type="text" maxlength="270" required />
        </div>

        <div class="form-group">
          <label for="artigo-tipo">Tipo *</label>
          <select id="artigo-tipo" v-model="form.tipo" required>
            <option value="" disabled>Selecione</option>
            <option v-for="t in opcoesTipo" :key="t.valor" :value="t.valor">
              {{ t.rotulo }}
            </option>
          </select>
        </div>

        <div class="form-group">
          <label for="artigo-qualis">Qualis</label>
          <select id="artigo-qualis" v-model="form.qualis">
            <option value="">Sem Qualis</option>
            <option v-for="q in opcoesQualis" :key="q" :value="q">{{ q }}</option>
          </select>
        </div>

        <div class="form-group">
          <label for="artigo-comprovante">Status do comprovante *</label>
          <select id="artigo-comprovante" v-model="form.status_comprovante" required>
            <option v-for="o in opcoesComprovante" :key="o.valor" :value="o.valor">
              {{ o.rotulo }}
            </option>
          </select>
        </div>

        <div class="form-group">
          <label for="artigo-data">Entrega do comprovante</label>
          <input id="artigo-data" v-model="form.data_entrega" type="date" />
        </div>

        <div class="form-group span-full">
          <label for="artigo-colegiado">Validação do colegiado *</label>
          <select id="artigo-colegiado" v-model="form.status_validacao_colegiado" required>
            <option v-for="o in opcoesColegiado" :key="o.valor" :value="o.valor">
              {{ o.rotulo }}
            </option>
          </select>
        </div>

        <p v-if="erroForm" class="aviso-erro span-full">{{ erroForm }}</p>
      </form>

      <template #rodape>
        <BaseButton type="button" variant="secondary" :disabled="salvando" @click="fecharModal">
          Cancelar
        </BaseButton>
        <BaseButton type="submit" form="form-artigo" variant="primary" :disabled="salvando">
          {{ salvando ? 'Salvando...' : 'Salvar' }}
        </BaseButton>
      </template>
    </BaseModal>
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
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
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
}

.tabela-rolagem {
  overflow-x: auto;
}

.tabela-simples {
  width: 100%;
  border-collapse: collapse;
}

.tabela-simples th {
  padding: 10px 12px;
  text-align: left;
  font-size: 0.8rem;
  font-weight: 600;
  color: #374151;
  background-color: #f9fafb;
  border-bottom: 1px solid #e5e7eb;
  white-space: nowrap;
}

.tabela-simples td {
  padding: 10px 12px;
  font-size: 0.9rem;
  color: #111827;
  border-bottom: 1px solid #e5e7eb;
  white-space: nowrap;
  vertical-align: top;
}

.tabela-simples td.coluna-titulo {
  min-width: 220px;
  max-width: 360px;
  white-space: normal;
}

.tabela-simples tbody tr:last-child td {
  border-bottom: none;
}

.coluna-acoes {
  text-align: right;
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

.botao-tabela:hover {
  background-color: #f9fafb;
  border-color: #9ca3af;
}

.botao-tabela:focus-visible {
  outline: 2px solid #3b82f6;
  outline-offset: 2px;
}

.visualmente-oculto {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}

.badge {
  display: inline-block;
  padding: 4px 10px;
  border-radius: 9999px;
  font-size: 0.75rem;
  font-weight: 600;
  white-space: nowrap;
}

.data-pequena {
  display: block;
  margin-top: 4px;
  font-size: 0.75rem;
  color: #6b7280;
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

.form-group input:focus,
.form-group select:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}
</style>
