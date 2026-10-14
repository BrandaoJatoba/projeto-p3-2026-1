<script setup>
import { ref, computed, onMounted } from 'vue'
import { useAuthStore } from '../stores/auth'
import DefaultLayout from '../layouts/DefaultLayout.vue'
import BaseButton from '../components/BaseButton.vue'

// ATENÇÃO: enquanto a API de professores não existe, a tela usa dados de exemplo.
// Trocar para false quando o GET /professores estiver disponível na dev.
const usarDadosDeExemplo = true

const dadosDeExemplo = [
  { id_professor: 1, nome_professor: 'Ana Beatriz Lima' },
  { id_professor: 2, nome_professor: 'José Carlos Almeida' },
  { id_professor: 3, nome_professor: 'Marina Souza' },
  { id_professor: 4, nome_professor: 'Rafael Tenório' },
  { id_professor: 5, nome_professor: 'Beatriz Nogueira' },
]

const authStore = useAuthStore()
const professores = ref([])
const carregando = ref(true)
const erro = ref(false)

const nomeForm = ref('')
const editandoId = ref(null)
const erroForm = ref('')
const salvando = ref(false)
const excluindo = ref({})
const podeExcluir = computed(() => {
  const perfis = authStore.usuario?.perfis ?? []
  return perfis.includes('ADMIN') || perfis.includes('SECRETARIA')
})

const textoBusca = ref('')
const colunaOrdenacao = ref('nome_professor')
const direcaoOrdenacao = ref('asc')

const aviso = ref(null)
let temporizadorAviso = null

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

const professoresVisiveis = computed(() => {
  const busca = normalizar(textoBusca.value.trim())

  return professores.value
    .filter((p) => normalizar(p.nome_professor).includes(busca))
    .sort((a, b) => {
      const comparacao = normalizar(a[colunaOrdenacao.value]).localeCompare(
        normalizar(b[colunaOrdenacao.value]),
        'pt-BR',
      )
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

async function buscarProfessores() {
  carregando.value = true
  erro.value = false

  if (usarDadosDeExemplo) {
    professores.value = [...dadosDeExemplo]
    carregando.value = false
    return
  }

  try {
    const resposta = await fetch('http://localhost:8000/professores', {
      headers: { Authorization: `Bearer ${authStore.token}` },
    })

    if (!resposta.ok) {
      erro.value = true
      return
    }

    professores.value = await resposta.json()
  } catch (e) {
    erro.value = true
  } finally {
    carregando.value = false
  }
}

function iniciarEdicao(professor) {
  editandoId.value = professor.id_professor
  nomeForm.value = professor.nome_professor
  erroForm.value = ''
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

function cancelarEdicao() {
  editandoId.value = null
  nomeForm.value = ''
  erroForm.value = ''
}

async function salvarProfessor() {
  const nome = nomeForm.value.trim()
  if (!nome) {
    erroForm.value = 'Informe o nome do professor.'
    return
  }

  erroForm.value = ''
  const editando = editandoId.value !== null

  if (usarDadosDeExemplo) {
    if (editando) {
      const professor = professores.value.find((p) => p.id_professor === editandoId.value)
      professor.nome_professor = nome
    } else {
      const maiorId = Math.max(0, ...professores.value.map((p) => p.id_professor))
      professores.value.push({ id_professor: maiorId + 1, nome_professor: nome })
    }
    textoBusca.value = ''
    mostrarAviso(editando ? 'Professor atualizado.' : 'Professor cadastrado.', 'sucesso')
    cancelarEdicao()
    return
  }

  salvando.value = true
  const url = editando
    ? `http://localhost:8000/professores/${editandoId.value}`
    : 'http://localhost:8000/professores'

  try {
    const resposta = await fetch(url, {
      method: editando ? 'PUT' : 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${authStore.token}`,
      },
      body: JSON.stringify({ nome_professor: nome }),
    })

    if (!resposta.ok) {
      erroForm.value = 'Não foi possível salvar o professor. Confira os dados.'
      return
    }

    await buscarProfessores()
    textoBusca.value = ''
    mostrarAviso(editando ? 'Professor atualizado.' : 'Professor cadastrado.', 'sucesso')
    cancelarEdicao()
  } catch (e) {
    erroForm.value = 'Não foi possível conectar ao servidor.'
  } finally {
    salvando.value = false
  }
}

async function excluirProfessor(professor) {
  const confirmar = confirm(
    `Excluir o professor ${professor.nome_professor}? Essa ação não pode ser desfeita.`,
  )
  if (!confirmar) return

  if (usarDadosDeExemplo) {
    professores.value = professores.value.filter((p) => p.id_professor !== professor.id_professor)
    if (editandoId.value === professor.id_professor) cancelarEdicao()
    mostrarAviso('Professor excluído.', 'sucesso')
    return
  }

  excluindo.value[professor.id_professor] = true

  try {
    const resposta = await fetch(`http://localhost:8000/professores/${professor.id_professor}`, {
      method: 'DELETE',
      headers: { Authorization: `Bearer ${authStore.token}` },
    })

    if (resposta.status === 403) {
      mostrarAviso('Você não tem permissão para excluir professores.', 'erro')
      return
    }

    if (!resposta.ok) {
      mostrarAviso(
        'Não foi possível excluir o professor. Ele pode estar vinculado a discentes.',
        'erro',
      )
      return
    }

    if (editandoId.value === professor.id_professor) cancelarEdicao()
    await buscarProfessores()
    mostrarAviso('Professor excluído.', 'sucesso')
  } catch (e) {
    mostrarAviso('Não foi possível conectar ao servidor.', 'erro')
  } finally {
    excluindo.value[professor.id_professor] = false
  }
}

onMounted(() => {
  buscarProfessores()
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
      <h1>Professores</h1>
    </div>

    <p v-if="usarDadosDeExemplo" class="aviso-exemplo">
      Dados de exemplo: a API de professores ainda não está conectada.
    </p>

    <div class="form-card">
      <h2>{{ editandoId ? 'Editar professor' : 'Novo professor' }}</h2>

      <form @submit.prevent="salvarProfessor">
        <div class="form-group">
          <label>Nome do professor</label>
          <input v-model="nomeForm" type="text" class="form-control" required />
        </div>

        <p v-if="erroForm" class="aviso-erro aviso-form">{{ erroForm }}</p>

        <div class="form-actions">
          <BaseButton type="submit" variant="primary" :disabled="salvando">
            {{ editandoId ? 'Salvar edição' : 'Cadastrar professor' }}
          </BaseButton>
          <BaseButton v-if="editandoId" type="button" variant="secondary" @click="cancelarEdicao">
            Cancelar
          </BaseButton>
        </div>
      </form>
    </div>

    <div class="tabela-card">
      <div class="tabela-topo">
        <h2>Corpo docente</h2>
        <input
          v-model="textoBusca"
          type="search"
          class="form-control campo-busca"
          placeholder="Buscar por nome..."
        />
      </div>

      <div v-if="carregando" class="linha-aviso">
        <p class="aviso-vazio">Carregando professores...</p>
      </div>
      <div v-else-if="erro" class="linha-aviso">
        <p class="aviso-erro">Não foi possível carregar os professores.</p>
      </div>
      <div v-else-if="professores.length === 0" class="linha-aviso">
        <p class="aviso-vazio">Nenhum professor cadastrado.</p>
      </div>
      <div v-else-if="professoresVisiveis.length === 0" class="linha-aviso">
        <p class="aviso-vazio">Nenhum professor encontrado para "{{ textoBusca }}".</p>
      </div>
      <table v-else>
        <thead>
          <tr>
            <th class="ordenavel" @click="ordenarPor('nome_professor')">
              Nome {{ indicadorOrdenacao('nome_professor') }}
            </th>
            <th class="coluna-acoes">Ações</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="professor in professoresVisiveis" :key="professor.id_professor">
            <td>{{ professor.nome_professor }}</td>
            <td class="coluna-acoes">
              <div class="acoes">
                <BaseButton type="button" variant="secondary" @click="iniciarEdicao(professor)">
                  Editar
                </BaseButton>
                <BaseButton
                  v-if="podeExcluir"
                  type="button"
                  variant="danger"
                  :disabled="excluindo[professor.id_professor]"
                  @click="excluirProfessor(professor)"
                >
                  Excluir
                </BaseButton>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </DefaultLayout>
</template>

<style scoped>
.page-header h1 {
  font-size: 1.8rem;
  color: #111827;
  margin-bottom: 24px;
}

.aviso-exemplo {
  padding: 12px 16px;
  background-color: #fffbeb;
  color: #92400e;
  border: 1px solid #fde68a;
  border-radius: 6px;
  font-size: 0.95rem;
  margin: 0 0 16px 0;
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
  width: 280px;
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
</style>
