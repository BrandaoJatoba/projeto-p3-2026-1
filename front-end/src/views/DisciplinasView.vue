<script setup>
import { ref, computed, onMounted } from 'vue'
import { useAuthStore } from '../stores/auth'
import DefaultLayout from '../layouts/DefaultLayout.vue'
import BaseButton from '../components/BaseButton.vue'

// Valores iguais aos do backend (back-end/db/enumStatus.py).
// NaturezaDisciplina: o tipo da disciplina.
const opcoesNatureza = [
  { valor: 'BASICAS', rotulo: 'Básicas' },
  { valor: 'ELETIVAS', rotulo: 'Eletivas' },
  { valor: 'TOPICOS_ESPECIAIS', rotulo: 'Tópicos especiais' },
  { valor: 'ESTUDO_DIRIGIDO', rotulo: 'Estudo dirigido' },
  { valor: 'DOCENCIA', rotulo: 'Docência' },
]

// GrupoPesquisa: o grupo de pesquisa ao qual a disciplina pertence.
const opcoesGrupo = [
  { valor: 'GRUPO 1', rotulo: 'Grupo 1', descricao: 'Teoria da Computação' },
  { valor: 'GRUPO 2', rotulo: 'Grupo 2', descricao: 'Metodologia e Técnicas de Computação' },
  { valor: 'GRUPO 3', rotulo: 'Grupo 3', descricao: 'Sistemas de Computação' },
  { valor: 'GRUPO 4', rotulo: 'Grupo 4', descricao: 'Outros' },
]

const authStore = useAuthStore()
const disciplinas = ref([])
const carregando = ref(true)
const erro = ref(false)

const codigoForm = ref('')
const nomeForm = ref('')
const naturezaForm = ref('')
const grupoForm = ref('')
const creditosForm = ref('')
const obrigatoriaForm = ref(false)
const editandoId = ref(null)
const erroForm = ref('')
const salvando = ref(false)
const excluindo = ref({})

const textoBusca = ref('')
const colunaOrdenacao = ref('nome_disciplina')
const direcaoOrdenacao = ref('asc')

const aviso = ref(null)
let temporizadorAviso = null

const podeExcluir = computed(() => {
  const perfis = authStore.usuario?.perfis ?? []
  return perfis.includes('ADMIN') || perfis.includes('SECRETARIA')
})

function mostrarAviso(texto, tipo) {
  aviso.value = { texto, tipo }
  clearTimeout(temporizadorAviso)
  temporizadorAviso = setTimeout(() => {
    aviso.value = null
  }, 3000)
}

function normalizar(texto) {
  return String(texto ?? '')
    .toLowerCase()
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
}

// Para comparar códigos: sem espaços e em maiúsculas ("ppgi 001" = "PPGI001").
function normalizarCodigo(texto) {
  return String(texto ?? '')
    .replace(/\s+/g, '')
    .toUpperCase()
}

function rotuloNatureza(valor) {
  const natureza = opcoesNatureza.find((n) => n.valor === valor)
  return natureza ? natureza.rotulo : valor || '—'
}

function buscarGrupo(valor) {
  return opcoesGrupo.find((g) => g.valor === valor)
}

function rotuloGrupo(valor) {
  return buscarGrupo(valor)?.rotulo || valor || '—'
}

function descricaoGrupo(valor) {
  return buscarGrupo(valor)?.descricao || ''
}

// O que cada coluna usa para ordenar.
function valorOrdenacao(disciplina, coluna) {
  if (coluna === 'creditos') return Number(disciplina.creditos)
  if (coluna === 'eh_obrigatoria') return disciplina.eh_obrigatoria ? 1 : 0
  if (coluna === 'natureza_disciplina')
    return normalizar(rotuloNatureza(disciplina.natureza_disciplina))
  if (coluna === 'grupo_disciplina') return normalizar(rotuloGrupo(disciplina.grupo_disciplina))
  return normalizar(disciplina[coluna])
}

const disciplinasVisiveis = computed(() => {
  const busca = normalizar(textoBusca.value.trim())

  return disciplinas.value
    .filter(
      (d) =>
        normalizar(d.nome_disciplina).includes(busca) ||
        normalizar(d.codigo_disciplina).includes(busca) ||
        normalizar(rotuloNatureza(d.natureza_disciplina)).includes(busca) ||
        normalizar(rotuloGrupo(d.grupo_disciplina)).includes(busca) ||
        normalizar(descricaoGrupo(d.grupo_disciplina)).includes(busca),
    )
    .sort((a, b) => {
      const coluna = colunaOrdenacao.value
      const valorA = valorOrdenacao(a, coluna)
      const valorB = valorOrdenacao(b, coluna)

      const comparacao =
        typeof valorA === 'number'
          ? valorA - valorB
          : String(valorA).localeCompare(String(valorB), 'pt-BR')

      return direcaoOrdenacao.value === 'asc' ? comparacao : -comparacao
    })
})

function ordenarPor(coluna) {
  if (colunaOrdenacao.value === coluna) {
    direcaoOrdenacao.value = direcaoOrdenacao.value === 'asc' ? 'desc' : 'asc'
  } else {
    colunaOrdenacao.value = coluna
    direcaoOrdenacao.value = 'asc'
  }
}

function indicadorOrdenacao(coluna) {
  if (colunaOrdenacao.value !== coluna) return ''
  return direcaoOrdenacao.value === 'asc' ? '▲' : '▼'
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

async function buscarDisciplinas() {
  carregando.value = true
  erro.value = false

  try {
    const resposta = await fetch('http://localhost:8000/disciplinas?limit=200', {
      headers: { Authorization: `Bearer ${authStore.token}` },
    })

    if (!resposta.ok) {
      erro.value = true
      return
    }

    disciplinas.value = await resposta.json()
  } catch {
    erro.value = true
  } finally {
    carregando.value = false
  }
}

function validarFormulario() {
  if (!codigoForm.value.trim()) return 'Informe o código da disciplina.'

  const codigoNovo = normalizarCodigo(codigoForm.value)
  const repetida = disciplinas.value.find(
    (d) =>
      d.id_disciplina !== editandoId.value && normalizarCodigo(d.codigo_disciplina) === codigoNovo,
  )
  if (repetida) return `Já existe uma disciplina com o código ${repetida.codigo_disciplina}.`

  if (!nomeForm.value.trim()) return 'Informe o nome da disciplina.'
  if (!naturezaForm.value) return 'Escolha a natureza da disciplina.'
  if (!grupoForm.value) return 'Escolha o grupo da disciplina.'

  const creditos = Number(creditosForm.value)
  if (creditosForm.value === '' || !Number.isInteger(creditos) || creditos < 1) {
    return 'Os créditos precisam ser um número inteiro maior que 0.'
  }

  return ''
}

function iniciarEdicao(disciplina) {
  editandoId.value = disciplina.id_disciplina
  codigoForm.value = disciplina.codigo_disciplina
  nomeForm.value = disciplina.nome_disciplina
  naturezaForm.value = disciplina.natureza_disciplina || ''
  grupoForm.value = disciplina.grupo_disciplina || ''
  creditosForm.value = disciplina.creditos
  obrigatoriaForm.value = Boolean(disciplina.eh_obrigatoria)
  erroForm.value = ''
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

function cancelarEdicao() {
  editandoId.value = null
  codigoForm.value = ''
  nomeForm.value = ''
  naturezaForm.value = ''
  grupoForm.value = ''
  creditosForm.value = ''
  obrigatoriaForm.value = false
  erroForm.value = ''
}

async function salvarDisciplina() {
  erroForm.value = validarFormulario()
  if (erroForm.value) return

  const editando = editandoId.value !== null
  const dados = {
    codigo_disciplina: codigoForm.value.trim(),
    nome_disciplina: nomeForm.value.trim(),
    natureza_disciplina: naturezaForm.value,
    grupo_disciplina: grupoForm.value,
    creditos: Number(creditosForm.value),
    eh_obrigatoria: obrigatoriaForm.value,
  }

  salvando.value = true
  const url = editando
    ? `http://localhost:8000/disciplinas/${editandoId.value}`
    : 'http://localhost:8000/disciplinas'

  try {
    const resposta = await fetch(url, {
      method: editando ? 'PUT' : 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${authStore.token}`,
      },
      body: JSON.stringify(dados),
    })

    if (!resposta.ok) {
      const detalhe = await lerMensagemDeErro(resposta)
      erroForm.value = detalhe || 'Não foi possível salvar a disciplina. Confira os dados.'
      return
    }

    await buscarDisciplinas()
    textoBusca.value = ''
    mostrarAviso(editando ? 'Disciplina atualizada.' : 'Disciplina cadastrada.', 'sucesso')
    cancelarEdicao()
  } catch {
    erroForm.value = 'Não foi possível conectar ao servidor.'
  } finally {
    salvando.value = false
  }
}

async function excluirDisciplina(disciplina) {
  const confirmar = confirm(
    `Excluir a disciplina ${disciplina.nome_disciplina}? Essa ação não pode ser desfeita.`,
  )
  if (!confirmar) return

  excluindo.value[disciplina.id_disciplina] = true

  try {
    const resposta = await fetch(`http://localhost:8000/disciplinas/${disciplina.id_disciplina}`, {
      method: 'DELETE',
      headers: { Authorization: `Bearer ${authStore.token}` },
    })

    if (resposta.status === 403) {
      mostrarAviso('Você não tem permissão para excluir disciplinas.', 'erro')
      return
    }

    if (!resposta.ok) {
      mostrarAviso(
        'Não foi possível excluir a disciplina. Ela pode estar no histórico de discentes.',
        'erro',
      )
      return
    }

    if (editandoId.value === disciplina.id_disciplina) cancelarEdicao()
    await buscarDisciplinas()
    mostrarAviso('Disciplina excluída.', 'sucesso')
  } catch {
    mostrarAviso('Não foi possível conectar ao servidor.', 'erro')
  } finally {
    excluindo.value[disciplina.id_disciplina] = false
  }
}

onMounted(() => {
  buscarDisciplinas()
})
</script>

<template>
  <DefaultLayout>
    <div
      v-if="aviso"
      class="aviso-flutuante"
      :class="aviso.tipo === 'sucesso' ? 'aviso-sucesso' : 'aviso-erro'"
    >
      {{ aviso.texto }}
    </div>

    <div class="page-header">
      <h1>Disciplinas</h1>
    </div>

    <div class="form-card">
      <h2>{{ editandoId ? 'Editar disciplina' : 'Nova disciplina' }}</h2>

      <form @submit.prevent="salvarDisciplina">
        <div class="form-grid">
          <div class="form-group">
            <label for="disciplina-codigo">Código</label>
            <input
              id="disciplina-codigo"
              v-model="codigoForm"
              type="text"
              maxlength="20"
              class="form-control"
              required
            />
          </div>

          <div class="form-group">
            <label for="disciplina-nome">Nome da disciplina</label>
            <input
              id="disciplina-nome"
              v-model="nomeForm"
              type="text"
              maxlength="150"
              class="form-control"
              required
            />
          </div>

          <div class="form-group">
            <label for="disciplina-natureza">Natureza</label>
            <select id="disciplina-natureza" v-model="naturezaForm" class="form-control" required>
              <option value="" disabled>Selecione a natureza</option>
              <option v-for="n in opcoesNatureza" :key="n.valor" :value="n.valor">
                {{ n.rotulo }}
              </option>
            </select>
          </div>

          <div class="form-group">
            <label for="disciplina-grupo">Grupo</label>
            <select id="disciplina-grupo" v-model="grupoForm" class="form-control" required>
              <option value="" disabled>Selecione o grupo</option>
              <option v-for="g in opcoesGrupo" :key="g.valor" :value="g.valor">
                {{ g.rotulo }} – {{ g.descricao }}
              </option>
            </select>
          </div>

          <div class="form-group">
            <label for="disciplina-creditos">Créditos</label>
            <input
              id="disciplina-creditos"
              v-model="creditosForm"
              type="number"
              min="1"
              step="1"
              class="form-control"
              required
            />
          </div>

          <div class="form-group-checkbox">
            <input id="disciplina-obrigatoria" v-model="obrigatoriaForm" type="checkbox" />
            <label for="disciplina-obrigatoria">Disciplina obrigatória</label>
          </div>
        </div>

        <p v-if="erroForm" class="aviso-erro aviso-form">{{ erroForm }}</p>

        <div class="form-actions">
          <BaseButton type="submit" variant="primary" :disabled="salvando">
            {{ editandoId ? 'Salvar edição' : 'Cadastrar disciplina' }}
          </BaseButton>
          <BaseButton v-if="editandoId" type="button" variant="secondary" @click="cancelarEdicao">
            Cancelar
          </BaseButton>
        </div>
      </form>
    </div>

    <div class="tabela-card">
      <div class="tabela-topo">
        <h2>Catálogo de disciplinas</h2>
        <input
          v-model="textoBusca"
          type="search"
          class="form-control campo-busca"
          placeholder="Buscar por nome, código, natureza ou grupo..."
          aria-label="Buscar disciplinas"
        />
      </div>

      <div v-if="carregando" class="linha-aviso">
        <p class="aviso-vazio">Carregando disciplinas...</p>
      </div>
      <div v-else-if="erro" class="linha-aviso">
        <p class="aviso-erro">Não foi possível carregar as disciplinas.</p>
      </div>
      <div v-else-if="disciplinas.length === 0" class="linha-aviso">
        <p class="aviso-vazio">Nenhuma disciplina cadastrada.</p>
      </div>
      <div v-else-if="disciplinasVisiveis.length === 0" class="linha-aviso">
        <p class="aviso-vazio">Nenhuma disciplina encontrada para "{{ textoBusca }}".</p>
      </div>
      <div v-else class="tabela-rolagem">
        <table>
          <thead>
            <tr>
              <th class="ordenavel" @click="ordenarPor('codigo_disciplina')">
                Código {{ indicadorOrdenacao('codigo_disciplina') }}
              </th>
              <th class="ordenavel" @click="ordenarPor('nome_disciplina')">
                Nome {{ indicadorOrdenacao('nome_disciplina') }}
              </th>
              <th class="ordenavel" @click="ordenarPor('natureza_disciplina')">
                Natureza {{ indicadorOrdenacao('natureza_disciplina') }}
              </th>
              <th class="ordenavel" @click="ordenarPor('grupo_disciplina')">
                Grupo {{ indicadorOrdenacao('grupo_disciplina') }}
              </th>
              <th class="ordenavel" @click="ordenarPor('creditos')">
                Créditos {{ indicadorOrdenacao('creditos') }}
              </th>
              <th class="ordenavel" @click="ordenarPor('eh_obrigatoria')">
                Obrigatória {{ indicadorOrdenacao('eh_obrigatoria') }}
              </th>
              <th class="coluna-acoes">Ações</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="disciplina in disciplinasVisiveis" :key="disciplina.id_disciplina">
              <td>{{ disciplina.codigo_disciplina }}</td>
              <td>{{ disciplina.nome_disciplina }}</td>
              <td>
                <span class="badge-natureza">
                  {{ rotuloNatureza(disciplina.natureza_disciplina) }}
                </span>
              </td>
              <td>
                <span class="badge-grupo" :title="descricaoGrupo(disciplina.grupo_disciplina)">
                  {{ rotuloGrupo(disciplina.grupo_disciplina) }}
                </span>
              </td>
              <td>{{ disciplina.creditos }}</td>
              <td>{{ disciplina.eh_obrigatoria ? 'Sim' : 'Não' }}</td>
              <td class="coluna-acoes">
                <div class="acoes">
                  <BaseButton type="button" variant="secondary" @click="iniciarEdicao(disciplina)">
                    Editar
                  </BaseButton>
                  <BaseButton
                    v-if="podeExcluir"
                    type="button"
                    variant="danger"
                    :disabled="excluindo[disciplina.id_disciplina]"
                    @click="excluirDisciplina(disciplina)"
                  >
                    Excluir
                  </BaseButton>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </DefaultLayout>
</template>

<style scoped>
.page-header h1 {
  font-size: 1.8rem;
  color: #111827;
  margin-bottom: 24px;
}

.form-card {
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 24px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  margin-bottom: 32px;
}
.form-card h2 {
  font-size: 1.25rem;
  color: #374151;
  margin: 0 0 16px 0;
  border-bottom: 1px solid #e5e7eb;
  padding-bottom: 8px;
}
.form-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
}
.form-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.form-group label {
  font-size: 0.875rem;
  font-weight: 500;
  color: #4b5563;
}
.form-group-checkbox {
  display: flex;
  align-items: center;
  gap: 8px;
  align-self: end;
  padding-bottom: 10px;
}
.form-group-checkbox label {
  font-size: 0.9rem;
  color: #374151;
  cursor: pointer;
}
.form-control {
  padding: 10px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 1rem;
  font-family: inherit;
  transition:
    border-color 0.2s,
    box-shadow 0.2s;
}
.form-control:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}
.form-actions {
  display: flex;
  gap: 12px;
  margin-top: 24px;
}
.aviso-form {
  margin-top: 16px;
}

.tabela-card {
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  overflow: hidden;
}
.tabela-topo {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 20px;
}
.tabela-topo h2 {
  font-size: 1.25rem;
  color: #374151;
  margin: 0;
}
.campo-busca {
  width: 320px;
  max-width: 100%;
}
.tabela-rolagem {
  overflow-x: auto;
}

.linha-aviso {
  padding: 0 20px 20px 20px;
}
.aviso-erro {
  padding: 12px 16px;
  background-color: #fef2f2;
  color: #b91c1c;
  border: 1px solid #fecaca;
  border-radius: 6px;
  font-size: 0.95rem;
  margin: 0;
}
.aviso-sucesso {
  padding: 12px 16px;
  background-color: #ecfdf5;
  color: #065f46;
  border: 1px solid #a7f3d0;
  border-radius: 6px;
  font-size: 0.95rem;
  margin: 0;
}
.aviso-flutuante {
  position: fixed;
  top: 80px;
  right: 24px;
  z-index: 50;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}
.aviso-vazio {
  color: #6b7280;
  font-style: italic;
  margin: 0;
}

table {
  width: 100%;
  border-collapse: collapse;
}
th {
  background-color: #f9fafb;
  color: #374151;
  font-weight: 600;
  text-align: left;
  padding: 12px 20px;
  border-top: 1px solid #e5e7eb;
  border-bottom: 1px solid #e5e7eb;
  font-size: 0.875rem;
  white-space: nowrap;
}
td {
  padding: 14px 20px;
  border-bottom: 1px solid #e5e7eb;
  color: #4b5563;
  font-size: 0.95rem;
}
tbody tr:last-child td {
  border-bottom: none;
}
.ordenavel {
  cursor: pointer;
  user-select: none;
}
.ordenavel:hover {
  background-color: #f3f4f6;
}
.coluna-acoes {
  text-align: right;
  width: 240px;
}
.acoes {
  display: flex;
  gap: 8px;
  justify-content: flex-end;
}

.badge-natureza,
.badge-grupo {
  display: inline-block;
  padding: 2px 10px;
  border-radius: 999px;
  font-size: 0.8rem;
  font-weight: 500;
  white-space: nowrap;
}
.badge-natureza {
  background-color: #eff6ff;
  color: #1e40af;
}
.badge-grupo {
  background-color: #f5f3ff;
  color: #5b21b6;
}
</style>
