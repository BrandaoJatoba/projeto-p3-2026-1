<script setup>
import { ref, computed, watch } from 'vue'
import BaseButton from '../BaseButton.vue'
import BaseModal from '../BaseModal.vue'
import { useAuthStore } from '../../stores/auth'

const props = defineProps({
  idEstudante: { type: Number, required: true },
  idOrientador: { type: Number, default: null },
})

const emit = defineEmits(['aviso'])

const api = 'http://localhost:8000'
const authStore = useAuthStore()

// Valores iguais aos do backend (back-end/db/enumStatus.py).
const opcoesStatusProposta = [
  { valor: 'PENDENTE', rotulo: 'Pendente', classe: 'situacao-pendente' },
  { valor: 'SUBMETIDA', rotulo: 'Submetida', classe: 'situacao-submetida' },
  { valor: 'APROVADA', rotulo: 'Aprovada', classe: 'situacao-aprovada' },
  { valor: 'DISPENSA', rotulo: 'Dispensa', classe: 'situacao-dispensa' },
  { valor: 'CANCELADO', rotulo: 'Cancelada', classe: 'situacao-cancelada' },
]
const opcoesStatusRelatorio = [
  { valor: 'PENDENTE', rotulo: 'Pendente', classe: 'situacao-pendente' },
  { valor: 'SUBMETIDO', rotulo: 'Submetido', classe: 'situacao-submetida' },
  { valor: 'APROVADO', rotulo: 'Aprovado', classe: 'situacao-aprovada' },
]

const estagios = ref([])
const carregando = ref(false)
const erro = ref('')

const professores = ref([])
const disciplinas = ref([])
const semestres = ref([])

const modalAberto = ref(false)
const salvando = ref(false)
const erroForm = ref('')
const editandoId = ref(null)
const form = ref({})

const professoresOrdenados = computed(() =>
  [...professores.value].sort((a, b) => a.nome_professor.localeCompare(b.nome_professor, 'pt-BR')),
)
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
const estagiosOrdenados = computed(() =>
  [...estagios.value].sort((a, b) => {
    const porSemestre = codigoSemestre(b.id_semestre).localeCompare(
      codigoSemestre(a.id_semestre),
      'pt-BR',
    )
    return porSemestre !== 0 ? porSemestre : b.id_estagio - a.id_estagio
  }),
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

function nomeProfessor(id) {
  return professores.value.find((p) => p.id_professor === id)?.nome_professor || `Professor ${id}`
}

function nomeDisciplina(id) {
  const disciplina = disciplinas.value.find((d) => d.id_disciplina === id)
  return disciplina
    ? `${disciplina.codigo_disciplina} – ${disciplina.nome_disciplina}`
    : `Disciplina ${id}`
}

function codigoSemestre(id) {
  return String(semestres.value.find((s) => s.id_semestre === id)?.codigo_semestre || id)
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

async function buscarLista(caminho, destino) {
  try {
    const resposta = await fetch(`${api}${caminho}`, { headers: cabecalho() })
    if (!resposta.ok) return
    destino.value = await resposta.json()
  } catch {
    // Sem a lista, a tabela mostra os números no lugar dos nomes.
  }
}

async function buscarEstagios() {
  carregando.value = true
  erro.value = ''
  try {
    const resposta = await fetch(`${api}/estagios/estudante/${props.idEstudante}`, {
      headers: cabecalho(),
    })
    if (resposta.status === 404) {
      estagios.value = []
      return
    }
    if (!resposta.ok) {
      erro.value = 'Não foi possível carregar os estágios.'
      return
    }
    estagios.value = await resposta.json()
  } catch {
    erro.value = 'Não foi possível carregar os estágios.'
  } finally {
    carregando.value = false
  }
}

function abrirModal(estagio = null) {
  editandoId.value = estagio ? estagio.id_estagio : null
  form.value = estagio
    ? {
        id_semestre: estagio.id_semestre ?? '',
        id_disciplina: estagio.id_disciplina ?? '',
        id_professor_supervisor: estagio.id_professor_supervisor ?? '',
        status_proposta: estagio.status_proposta || 'PENDENTE',
        data_entrega_proposta: (estagio.data_entrega_proposta || '').slice(0, 10),
        status_relatorio: estagio.status_relatorio || 'PENDENTE',
        data_entrega_relatorio: (estagio.data_entrega_relatorio || '').slice(0, 10),
      }
    : {
        id_semestre: '',
        id_disciplina: '',
        id_professor_supervisor: props.idOrientador || '',
        status_proposta: 'PENDENTE',
        data_entrega_proposta: '',
        status_relatorio: 'PENDENTE',
        data_entrega_relatorio: '',
      }
  erroForm.value = ''
  modalAberto.value = true
}

function fecharModal() {
  if (salvando.value) return
  modalAberto.value = false
}

function validar() {
  if (!form.value.id_semestre) return 'Escolha o semestre do estágio.'
  if (!form.value.id_disciplina) return 'Escolha a disciplina do estágio.'
  if (!form.value.id_professor_supervisor) return 'Escolha o professor supervisor.'
  return ''
}

async function salvar() {
  erroForm.value = validar()
  if (erroForm.value) return

  const editando = editandoId.value !== null
  const dados = {
    id_estudante: props.idEstudante,
    id_semestre: Number(form.value.id_semestre),
    id_disciplina: Number(form.value.id_disciplina),
    id_professor_supervisor: Number(form.value.id_professor_supervisor),
    status_proposta: form.value.status_proposta,
    data_entrega_proposta: form.value.data_entrega_proposta || null,
    status_relatorio: form.value.status_relatorio,
    data_entrega_relatorio: form.value.data_entrega_relatorio || null,
  }
  const url = editando ? `${api}/estagios/${editandoId.value}` : `${api}/estagios`

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
        erroForm.value = 'Você não tem permissão para registrar estágios.'
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
    if (salvo && salvo.id_estagio) {
      estagios.value = editando
        ? estagios.value.map((e) => (e.id_estagio === salvo.id_estagio ? salvo : e))
        : [...estagios.value, salvo]
    } else {
      buscarEstagios()
    }

    modalAberto.value = false
    emit('aviso', editando ? 'Estágio atualizado.' : 'Estágio registrado.', 'sucesso')
  } catch {
    erroForm.value = 'Não foi possível conectar ao servidor.'
  } finally {
    salvando.value = false
  }
}

buscarLista('/professores?limit=200', professores)
buscarLista('/disciplinas?limit=200', disciplinas)
buscarLista('/configuracoes/semestres', semestres)

watch(() => props.idEstudante, buscarEstagios, { immediate: true })
</script>

<template>
  <section class="card">
    <div class="card-topo">
      <h2>Estágio docência</h2>
      <BaseButton type="button" variant="secondary" @click="abrirModal()">
        Adicionar estágio
      </BaseButton>
    </div>

    <p v-if="carregando" class="texto-vazio">Carregando estágios...</p>
    <p v-else-if="erro" class="aviso-erro">{{ erro }}</p>
    <p v-else-if="estagios.length === 0" class="texto-vazio">Nenhum estágio registrado.</p>
    <div v-else class="tabela-rolagem">
      <table class="tabela-simples">
        <thead>
          <tr>
            <th>Semestre</th>
            <th>Disciplina</th>
            <th>Supervisor</th>
            <th>Proposta</th>
            <th>Relatório</th>
            <th class="coluna-acoes"><span class="visualmente-oculto">Ações</span></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="estagio in estagiosOrdenados" :key="estagio.id_estagio">
            <td>{{ codigoSemestre(estagio.id_semestre) }}</td>
            <td>{{ nomeDisciplina(estagio.id_disciplina) }}</td>
            <td>{{ nomeProfessor(estagio.id_professor_supervisor) }}</td>
            <td>
              <span
                class="badge"
                :class="situacao(opcoesStatusProposta, estagio.status_proposta).classe"
              >
                {{ situacao(opcoesStatusProposta, estagio.status_proposta).rotulo }}
              </span>
              <span v-if="estagio.data_entrega_proposta" class="data-pequena">
                entregue em {{ formatarData(estagio.data_entrega_proposta) }}
              </span>
            </td>
            <td>
              <span
                class="badge"
                :class="situacao(opcoesStatusRelatorio, estagio.status_relatorio).classe"
              >
                {{ situacao(opcoesStatusRelatorio, estagio.status_relatorio).rotulo }}
              </span>
              <span v-if="estagio.data_entrega_relatorio" class="data-pequena">
                entregue em {{ formatarData(estagio.data_entrega_relatorio) }}
              </span>
            </td>
            <td class="coluna-acoes">
              <button
                type="button"
                class="botao-tabela"
                :aria-label="`Editar estágio de ${codigoSemestre(estagio.id_semestre)}`"
                @click="abrirModal(estagio)"
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
      :titulo="editandoId ? 'Editar estágio docência' : 'Adicionar estágio docência'"
      larguraMaxima="680px"
      @fechar="fecharModal"
    >
      <form id="form-estagio" class="form-grid" @submit.prevent="salvar">
        <div class="form-group">
          <label for="estagio-semestre">Semestre *</label>
          <select id="estagio-semestre" v-model="form.id_semestre" required>
            <option value="" disabled>Selecione</option>
            <option v-for="s in semestresOrdenados" :key="s.id_semestre" :value="s.id_semestre">
              {{ s.codigo_semestre }}
            </option>
          </select>
        </div>

        <div class="form-group">
          <label for="estagio-supervisor">Professor supervisor *</label>
          <select id="estagio-supervisor" v-model="form.id_professor_supervisor" required>
            <option value="" disabled>Selecione</option>
            <option v-for="p in professoresOrdenados" :key="p.id_professor" :value="p.id_professor">
              {{ p.nome_professor }}
            </option>
          </select>
        </div>

        <div class="form-group span-full">
          <label for="estagio-disciplina">Disciplina *</label>
          <select id="estagio-disciplina" v-model="form.id_disciplina" required>
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
          <label for="estagio-status-proposta">Status da proposta</label>
          <select id="estagio-status-proposta" v-model="form.status_proposta">
            <option v-for="o in opcoesStatusProposta" :key="o.valor" :value="o.valor">
              {{ o.rotulo }}
            </option>
          </select>
        </div>

        <div class="form-group">
          <label for="estagio-data-proposta">Entrega da proposta</label>
          <input id="estagio-data-proposta" v-model="form.data_entrega_proposta" type="date" />
        </div>

        <div class="form-group">
          <label for="estagio-status-relatorio">Status do relatório</label>
          <select id="estagio-status-relatorio" v-model="form.status_relatorio">
            <option v-for="o in opcoesStatusRelatorio" :key="o.valor" :value="o.valor">
              {{ o.rotulo }}
            </option>
          </select>
        </div>

        <div class="form-group">
          <label for="estagio-data-relatorio">Entrega do relatório</label>
          <input id="estagio-data-relatorio" v-model="form.data_entrega_relatorio" type="date" />
        </div>

        <p v-if="erroForm" class="aviso-erro span-full">{{ erroForm }}</p>
      </form>

      <template #rodape>
        <BaseButton type="button" variant="secondary" :disabled="salvando" @click="fecharModal">
          Cancelar
        </BaseButton>
        <BaseButton type="submit" form="form-estagio" variant="primary" :disabled="salvando">
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
  vertical-align: top;
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

.form-group input:focus,
.form-group select:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}
</style>
