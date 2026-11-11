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
const opcoesConceito = ['A', 'B', 'C', 'D']
const opcoesStatus = [
  { valor: 'PENDENTE', rotulo: 'Pendente', classe: 'situacao-pendente' },
  { valor: 'APROVADO', rotulo: 'Aprovado', classe: 'situacao-aprovada' },
  { valor: 'REPROVADO', rotulo: 'Reprovado', classe: 'situacao-cancelada' },
  { valor: 'CANCELADO', rotulo: 'Cancelado', classe: 'situacao-dispensa' },
]

const historico = ref([])
const carregando = ref(false)
const erro = ref('')

const disciplinas = ref([])
const semestres = ref([])

const modalAberto = ref(false)
const salvando = ref(false)
const erroForm = ref('')
const editandoId = ref(null)
const form = ref({})
// Linhas que estão sendo excluídas (para desativar o botão enquanto espera).
const excluindo = ref({})

const disciplinasOrdenadas = computed(() =>
  [...disciplinas.value].sort((a, b) =>
    String(a.codigo_disciplina).localeCompare(String(b.codigo_disciplina), 'pt-BR'),
  ),
)
const semestresOrdenados = computed(() =>
  [...semestres.value].sort((a, b) =>
    String(b.codigo_semestre).localeCompare(String(a.codigo_semestre), 'pt-BR'),
  ),
)
// Semestre mais recente primeiro; dentro do semestre, pelo código da disciplina.
const historicoOrdenado = computed(() =>
  [...historico.value].sort((a, b) => {
    const porSemestre = codigoSemestre(b.id_semestre).localeCompare(
      codigoSemestre(a.id_semestre),
      'pt-BR',
    )
    if (porSemestre !== 0) return porSemestre
    return nomeDisciplina(a.id_disciplina).localeCompare(nomeDisciplina(b.id_disciplina), 'pt-BR')
  }),
)

function cabecalho() {
  return { Authorization: `Bearer ${authStore.token}` }
}

function buscarDisciplina(id) {
  return disciplinas.value.find((d) => d.id_disciplina === id)
}

function nomeDisciplina(id) {
  const disciplina = buscarDisciplina(id)
  return disciplina
    ? `${disciplina.codigo_disciplina} – ${disciplina.nome_disciplina}`
    : `Disciplina ${id}`
}

function creditosDisciplina(id) {
  return buscarDisciplina(id)?.creditos ?? '—'
}

function codigoSemestre(id) {
  return String(semestres.value.find((s) => s.id_semestre === id)?.codigo_semestre || id)
}

function situacao(valor) {
  return (
    opcoesStatus.find((o) => o.valor === valor) || {
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

async function buscarLista(caminho, destino) {
  try {
    const resposta = await fetch(`${api}${caminho}`, { headers: cabecalho() })
    if (!resposta.ok) return
    destino.value = await resposta.json()
  } catch {
    // Sem a lista, a tabela mostra os números no lugar dos nomes.
  }
}

async function buscarHistorico() {
  carregando.value = true
  erro.value = ''
  try {
    const resposta = await fetch(`${api}/historico-disciplinas/estudante/${props.idEstudante}`, {
      headers: cabecalho(),
    })
    if (resposta.status === 404) {
      historico.value = []
      return
    }
    if (resposta.status === 401) {
      erro.value = 'Sua sessão expirou. Saia e entre de novo.'
      return
    }
    if (!resposta.ok) {
      erro.value = 'Não foi possível carregar as disciplinas cursadas.'
      return
    }
    const dados = await resposta.json()
    historico.value = Array.isArray(dados) ? dados : dados ? [dados] : []
  } catch {
    erro.value = 'Não foi possível carregar as disciplinas cursadas.'
  } finally {
    carregando.value = false
  }
}

function abrirModal(registro = null) {
  editandoId.value = registro ? registro.id_historico : null
  form.value = registro
    ? {
        id_disciplina: registro.id_disciplina ?? '',
        id_semestre: registro.id_semestre ?? '',
        conceito: registro.conceito || '',
        status_disciplina: registro.status_disciplina || 'PENDENTE',
      }
    : {
        id_disciplina: '',
        id_semestre: '',
        conceito: '',
        status_disciplina: 'PENDENTE',
      }
  erroForm.value = ''
  modalAberto.value = true
}

function fecharModal() {
  if (salvando.value) return
  modalAberto.value = false
}

// Mesma disciplina no mesmo semestre já registrada para este aluno?
function jaRegistrada() {
  const idDisciplina = Number(form.value.id_disciplina)
  const idSemestre = Number(form.value.id_semestre)
  return historico.value.some(
    (h) => h.id_disciplina === idDisciplina && h.id_semestre === idSemestre,
  )
}

function validar(editando) {
  if (editando) return ''
  if (!form.value.id_disciplina) return 'Escolha a disciplina.'
  if (!form.value.id_semestre) return 'Escolha o semestre letivo.'
  if (jaRegistrada()) return 'Essa disciplina já está registrada nesse semestre.'
  return ''
}

async function salvar() {
  const editando = editandoId.value !== null
  erroForm.value = validar(editando)
  if (erroForm.value) return

  // Na edição, a task pede para alterar só o conceito e o status.
  const dados = editando
    ? {
        conceito: form.value.conceito || null,
        status_disciplina: form.value.status_disciplina,
      }
    : {
        id_estudante: props.idEstudante,
        id_disciplina: Number(form.value.id_disciplina),
        id_semestre: Number(form.value.id_semestre),
        conceito: form.value.conceito || null,
        status_disciplina: form.value.status_disciplina,
      }
  const url = editando
    ? `${api}/historico-disciplinas/${editandoId.value}`
    : `${api}/historico-disciplinas`

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
        erroForm.value = 'Você não tem permissão para registrar disciplinas cursadas.'
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
    if (salvo && salvo.id_historico) {
      historico.value = editando
        ? historico.value.map((h) => (h.id_historico === salvo.id_historico ? salvo : h))
        : [...historico.value, salvo]
    } else {
      buscarHistorico()
    }

    modalAberto.value = false
    emit(
      'aviso',
      editando ? 'Registro atualizado com sucesso.' : 'Disciplina registrada.',
      'sucesso',
    )
  } catch {
    erroForm.value = 'Não foi possível conectar ao servidor.'
  } finally {
    salvando.value = false
  }
}

// Serve para corrigir um registro feito errado (disciplina ou semestre trocados),
// já que na edição esses dois campos ficam travados.
async function excluir(registro) {
  const descricao = `${nomeDisciplina(registro.id_disciplina)} de ${codigoSemestre(registro.id_semestre)}`
  const confirmar = confirm(`Excluir ${descricao}? Essa ação não pode ser desfeita.`)
  if (!confirmar) return

  excluindo.value[registro.id_historico] = true
  try {
    const resposta = await fetch(`${api}/historico-disciplinas/${registro.id_historico}`, {
      method: 'DELETE',
      headers: cabecalho(),
    })

    if (!resposta.ok) {
      if (resposta.status === 401) {
        emit('aviso', 'Sua sessão expirou. Saia e entre de novo.', 'erro')
      } else if (resposta.status === 403) {
        emit('aviso', 'Você não tem permissão para excluir disciplinas cursadas.', 'erro')
      } else {
        const detalhe = await lerMensagemDeErro(resposta)
        emit('aviso', detalhe || 'Não foi possível excluir a disciplina.', 'erro')
      }
      return
    }

    historico.value = historico.value.filter((h) => h.id_historico !== registro.id_historico)
    emit('aviso', 'Disciplina removida.', 'sucesso')
  } catch {
    emit('aviso', 'Não foi possível conectar ao servidor.', 'erro')
  } finally {
    excluindo.value[registro.id_historico] = false
  }
}

buscarLista('/disciplinas?limit=200', disciplinas)
buscarLista('/configuracoes/semestres', semestres)

watch(() => props.idEstudante, buscarHistorico, { immediate: true })
</script>

<template>
  <section class="card">
    <div class="card-topo">
      <h2>Disciplinas cursadas</h2>
      <BaseButton type="button" variant="secondary" @click="abrirModal()">
        Adicionar disciplina
      </BaseButton>
    </div>

    <p v-if="carregando" class="texto-vazio">Carregando disciplinas cursadas...</p>
    <p v-else-if="erro" class="aviso-erro">{{ erro }}</p>
    <p v-else-if="historico.length === 0" class="texto-vazio">Nenhuma disciplina registrada.</p>
    <div v-else class="tabela-rolagem">
      <table class="tabela-simples">
        <thead>
          <tr>
            <th>Semestre</th>
            <th>Disciplina</th>
            <th>Créditos</th>
            <th>Conceito</th>
            <th>Status</th>
            <th class="coluna-acoes"><span class="visualmente-oculto">Ações</span></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="registro in historicoOrdenado" :key="registro.id_historico">
            <td>{{ codigoSemestre(registro.id_semestre) }}</td>
            <td class="coluna-disciplina">{{ nomeDisciplina(registro.id_disciplina) }}</td>
            <td>{{ creditosDisciplina(registro.id_disciplina) }}</td>
            <td>{{ registro.conceito || '—' }}</td>
            <td>
              <span class="badge" :class="situacao(registro.status_disciplina).classe">
                {{ situacao(registro.status_disciplina).rotulo }}
              </span>
            </td>
            <td class="coluna-acoes">
              <div class="acoes-linha">
                <button
                  type="button"
                  class="botao-tabela"
                  :aria-label="`Editar ${nomeDisciplina(registro.id_disciplina)}`"
                  @click="abrirModal(registro)"
                >
                  <span aria-hidden="true">✎</span> Editar
                </button>
                <button
                  type="button"
                  class="botao-tabela botao-perigo"
                  :aria-label="`Excluir ${nomeDisciplina(registro.id_disciplina)}`"
                  :disabled="excluindo[registro.id_historico]"
                  @click="excluir(registro)"
                >
                  {{ excluindo[registro.id_historico] ? 'Excluindo...' : 'Excluir' }}
                </button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <BaseModal
      :aberto="modalAberto"
      :titulo="editandoId ? 'Editar disciplina cursada' : 'Adicionar disciplina cursada'"
      larguraMaxima="640px"
      @fechar="fecharModal"
    >
      <form id="form-historico" class="form-grid" @submit.prevent="salvar">
        <div class="form-group span-full">
          <label for="historico-disciplina">Disciplina *</label>
          <select
            id="historico-disciplina"
            v-model="form.id_disciplina"
            :required="!editandoId"
            :disabled="Boolean(editandoId)"
          >
            <option value="" disabled>Selecione</option>
            <option
              v-for="d in disciplinasOrdenadas"
              :key="d.id_disciplina"
              :value="d.id_disciplina"
            >
              {{ d.codigo_disciplina }} – {{ d.nome_disciplina }}
            </option>
          </select>
        </div>

        <div class="form-group">
          <label for="historico-semestre">Semestre letivo *</label>
          <select
            id="historico-semestre"
            v-model="form.id_semestre"
            :required="!editandoId"
            :disabled="Boolean(editandoId)"
          >
            <option value="" disabled>Selecione</option>
            <option v-for="s in semestresOrdenados" :key="s.id_semestre" :value="s.id_semestre">
              {{ s.codigo_semestre }}
            </option>
          </select>
        </div>

        <div class="form-group">
          <label for="historico-conceito">Conceito</label>
          <select id="historico-conceito" v-model="form.conceito">
            <option value="">Sem conceito</option>
            <option v-for="c in opcoesConceito" :key="c" :value="c">{{ c }}</option>
          </select>
        </div>

        <div class="form-group">
          <label for="historico-status">Status</label>
          <select id="historico-status" v-model="form.status_disciplina">
            <option v-for="o in opcoesStatus" :key="o.valor" :value="o.valor">
              {{ o.rotulo }}
            </option>
          </select>
        </div>

        <p v-if="editandoId" class="dica span-full">
          Na edição, só o conceito e o status podem ser alterados. Se a disciplina ou o semestre
          estiverem errados, exclua o registro e adicione de novo.
        </p>

        <p v-if="erroForm" class="aviso-erro span-full">{{ erroForm }}</p>
      </form>

      <template #rodape>
        <BaseButton type="button" variant="secondary" :disabled="salvando" @click="fecharModal">
          Cancelar
        </BaseButton>
        <BaseButton type="submit" form="form-historico" variant="primary" :disabled="salvando">
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

.dica {
  margin: 0;
  font-size: 0.8rem;
  color: #6b7280;
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

.tabela-simples td.coluna-disciplina {
  min-width: 220px;
  white-space: normal;
}

.tabela-simples tbody tr:last-child td {
  border-bottom: none;
}

.coluna-acoes {
  text-align: right;
}

.acoes-linha {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
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
  white-space: nowrap;
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

.botao-perigo {
  color: #b91c1c;
  border-color: #fecaca;
}

.botao-perigo:hover:not(:disabled) {
  background-color: #fef2f2;
  border-color: #f87171;
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

.situacao-aprovada {
  background-color: #ecfdf5;
  color: #065f46;
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

.form-group select:disabled {
  background-color: #f3f4f6;
  color: #6b7280;
}

.form-group input:focus,
.form-group select:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}
</style>
