<script setup>
import { ref, computed, onMounted } from 'vue'
import { useAuthStore } from '../stores/auth'
import DefaultLayout from '../layouts/DefaultLayout.vue'
import BaseButton from '../components/BaseButton.vue'

// ATENÇÃO: enquanto a API de disciplinas não existe, a tela usa dados de exemplo.
// Trocar para false quando o GET /disciplinas estiver disponível na dev.
const usarDadosDeExemplo = true

const dadosDeExemplo = [
  {
    id_disciplina: 1,
    codigo_disciplina: 'PPGI001',
    nome_disciplina: 'Metodologia de Pesquisa',
    grupo_disciplina: 'BASICAS',
    creditos: 4,
  },
  {
    id_disciplina: 2,
    codigo_disciplina: 'PPGI002',
    nome_disciplina: 'Redes de Computadores',
    grupo_disciplina: 'ELETIVAS',
    creditos: 4,
  },
  {
    id_disciplina: 3,
    codigo_disciplina: 'PPGI003',
    nome_disciplina: 'Banco de Dados Avançado',
    grupo_disciplina: 'ELETIVAS',
    creditos: 4,
  },
  {
    id_disciplina: 4,
    codigo_disciplina: 'PPGI004',
    nome_disciplina: 'Tópicos em Inteligência Artificial',
    grupo_disciplina: 'TOPICOS_ESPECIAIS',
    creditos: 4,
  },
  {
    id_disciplina: 5,
    codigo_disciplina: 'PPGI005',
    nome_disciplina: 'Estudo Dirigido I',
    grupo_disciplina: 'ESTUDO_DIRIGIDO',
    creditos: 2,
  },
  {
    id_disciplina: 6,
    codigo_disciplina: 'PPGI006',
    nome_disciplina: 'Estágio em Docência',
    grupo_disciplina: 'DOCENCIA',
    creditos: 2,
  },
]

// Valores do grupo conforme o documento de design (confirmar no /docs quando a API existir).
const gruposDisponiveis = [
  { valor: 'BASICAS', rotulo: 'Básicas' },
  { valor: 'ELETIVAS', rotulo: 'Eletivas' },
  { valor: 'TOPICOS_ESPECIAIS', rotulo: 'Tópicos especiais' },
  { valor: 'ESTUDO_DIRIGIDO', rotulo: 'Estudo dirigido' },
  { valor: 'DOCENCIA', rotulo: 'Docência' },
]

const authStore = useAuthStore()
const disciplinas = ref([])
const carregando = ref(true)
const erro = ref(false)

const codigoForm = ref('')
const nomeForm = ref('')
const grupoForm = ref('')
const creditosForm = ref('')
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

function rotuloGrupo(valor) {
  const grupo = gruposDisponiveis.find((g) => g.valor === valor)
  return grupo ? grupo.rotulo : valor
}

const disciplinasVisiveis = computed(() => {
  const busca = normalizar(textoBusca.value.trim())

  return disciplinas.value
    .filter(
      (d) =>
        normalizar(d.nome_disciplina).includes(busca) ||
        normalizar(d.codigo_disciplina).includes(busca) ||
        normalizar(rotuloGrupo(d.grupo_disciplina)).includes(busca),
    )
    .sort((a, b) => {
      const coluna = colunaOrdenacao.value
      let comparacao

      if (coluna === 'creditos') {
        comparacao = Number(a.creditos) - Number(b.creditos)
      } else if (coluna === 'grupo_disciplina') {
        comparacao = normalizar(rotuloGrupo(a.grupo_disciplina)).localeCompare(
          normalizar(rotuloGrupo(b.grupo_disciplina)),
          'pt-BR',
        )
      } else {
        comparacao = normalizar(a[coluna]).localeCompare(normalizar(b[coluna]), 'pt-BR')
      }

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

async function buscarDisciplinas() {
  carregando.value = true
  erro.value = false

  if (usarDadosDeExemplo) {
    disciplinas.value = dadosDeExemplo.map((d) => ({ ...d }))
    carregando.value = false
    return
  }

  try {
    const resposta = await fetch('http://localhost:8000/disciplinas', {
      headers: { Authorization: `Bearer ${authStore.token}` },
    })

    if (!resposta.ok) {
      erro.value = true
      return
    }

    disciplinas.value = await resposta.json()
  } catch (e) {
    erro.value = true
  } finally {
    carregando.value = false
  }
}

function validarFormulario() {
  if (!codigoForm.value.trim()) return 'Informe o código da disciplina.'
  if (!nomeForm.value.trim()) return 'Informe o nome da disciplina.'
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
  grupoForm.value = disciplina.grupo_disciplina
  creditosForm.value = disciplina.creditos
  erroForm.value = ''
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

function cancelarEdicao() {
  editandoId.value = null
  codigoForm.value = ''
  nomeForm.value = ''
  grupoForm.value = ''
  creditosForm.value = ''
  erroForm.value = ''
}

async function salvarDisciplina() {
  erroForm.value = validarFormulario()
  if (erroForm.value) return

  const editando = editandoId.value !== null
  const dados = {
    codigo_disciplina: codigoForm.value.trim(),
    nome_disciplina: nomeForm.value.trim(),
    grupo_disciplina: grupoForm.value,
    creditos: Number(creditosForm.value),
  }

  if (usarDadosDeExemplo) {
    if (editando) {
      const disciplina = disciplinas.value.find((d) => d.id_disciplina === editandoId.value)
      Object.assign(disciplina, dados)
    } else {
      const maiorId = Math.max(0, ...disciplinas.value.map((d) => d.id_disciplina))
      disciplinas.value.push({ id_disciplina: maiorId + 1, ...dados })
    }
    textoBusca.value = ''
    mostrarAviso(editando ? 'Disciplina atualizada.' : 'Disciplina cadastrada.', 'sucesso')
    cancelarEdicao()
    return
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
      erroForm.value = 'Não foi possível salvar a disciplina. Confira os dados.'
      return
    }

    await buscarDisciplinas()
    textoBusca.value = ''
    mostrarAviso(editando ? 'Disciplina atualizada.' : 'Disciplina cadastrada.', 'sucesso')
    cancelarEdicao()
  } catch (e) {
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

  if (usarDadosDeExemplo) {
    disciplinas.value = disciplinas.value.filter(
      (d) => d.id_disciplina !== disciplina.id_disciplina,
    )
    if (editandoId.value === disciplina.id_disciplina) cancelarEdicao()
    mostrarAviso('Disciplina excluída.', 'sucesso')
    return
  }

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
  } catch (e) {
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

    <p v-if="usarDadosDeExemplo" class="aviso-exemplo">
      Dados de exemplo: a API de disciplinas ainda não está conectada.
    </p>

    <div class="form-card">
      <h2>{{ editandoId ? 'Editar disciplina' : 'Nova disciplina' }}</h2>

      <form @submit.prevent="salvarDisciplina">
        <div class="form-grid">
          <div class="form-group">
            <label>Código</label>
            <input v-model="codigoForm" type="text" class="form-control" required />
          </div>

          <div class="form-group">
            <label>Nome da disciplina</label>
            <input v-model="nomeForm" type="text" class="form-control" required />
          </div>

          <div class="form-group">
            <label>Grupo</label>
            <select v-model="grupoForm" class="form-control" required>
              <option value="" disabled>Selecione um grupo</option>
              <option v-for="grupo in gruposDisponiveis" :key="grupo.valor" :value="grupo.valor">
                {{ grupo.rotulo }}
              </option>
            </select>
          </div>

          <div class="form-group">
            <label>Créditos</label>
            <input
              v-model="creditosForm"
              type="number"
              min="1"
              step="1"
              class="form-control"
              required
            />
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
          placeholder="Buscar por nome, código ou grupo..."
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
      <table v-else>
        <thead>
          <tr>
            <th class="ordenavel" @click="ordenarPor('codigo_disciplina')">
              Código {{ indicadorOrdenacao('codigo_disciplina') }}
            </th>
            <th class="ordenavel" @click="ordenarPor('nome_disciplina')">
              Nome {{ indicadorOrdenacao('nome_disciplina') }}
            </th>
            <th class="ordenavel" @click="ordenarPor('grupo_disciplina')">
              Grupo {{ indicadorOrdenacao('grupo_disciplina') }}
            </th>
            <th class="ordenavel" @click="ordenarPor('creditos')">
              Créditos {{ indicadorOrdenacao('creditos') }}
            </th>
            <th class="coluna-acoes">Ações</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="disciplina in disciplinasVisiveis" :key="disciplina.id_disciplina">
            <td>{{ disciplina.codigo_disciplina }}</td>
            <td>{{ disciplina.nome_disciplina }}</td>
            <td>
              <span class="badge-grupo">{{ rotuloGrupo(disciplina.grupo_disciplina) }}</span>
            </td>
            <td>{{ disciplina.creditos }}</td>
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
  width: 320px;
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

.badge-grupo {
  display: inline-block;
  padding: 2px 10px;
  border-radius: 999px;
  background-color: #eff6ff;
  color: #1e40af;
  font-size: 0.8rem;
  font-weight: 500;
}
</style>
