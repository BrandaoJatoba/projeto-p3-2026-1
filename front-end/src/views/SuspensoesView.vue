<script setup>
import { ref, onMounted } from 'vue'
import { useAuthStore } from '../stores/auth'
import DefaultLayout from '../layouts/DefaultLayout.vue'
import BaseButton from '../components/BaseButton.vue' // <-- Importando o botão

const idSemestreSuspensao = ref('')
const motivoSuspensao = ref('')
const dataInicioSuspensao = ref('')
const dataFimSuspensao = ref('')
const mensagemSuspensao = ref('')
const suspensoes = ref([])
const editandoSuspensaoId = ref(null)

const semestres = ref([])

const authStore = useAuthStore()

async function cadastrarSuspensao() {
  mensagemSuspensao.value = ''

  const dadosSuspensao = {
    id_semestre: idSemestreSuspensao.value,
    motivo: motivoSuspensao.value,
    data_inicio_suspensao: dataInicioSuspensao.value,
    data_fim_suspensao: dataFimSuspensao.value || null,
  }

  const editando = editandoSuspensaoId.value !== null
  const url = editando
    ? `http://localhost:8000/configuracoes/suspensoes/${editandoSuspensaoId.value}`
    : 'http://localhost:8000/configuracoes/suspensoes'
  const metodo = editando ? 'PUT' : 'POST'

  try {
    const resposta = await fetch(url, {
      method: metodo,
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${authStore.token}`,
      },
      body: JSON.stringify(dadosSuspensao),
    })

    if (!resposta.ok) {
      mensagemSuspensao.value = 'Erro ao salvar suspensão. Confira os dados.'
      return
    }

    mensagemSuspensao.value = editando
      ? 'Suspensão atualizada com sucesso!'
      : 'Suspensão cadastrada com sucesso!'
    cancelarEdicaoSuspensao()
    buscarSuspensoes()
  } catch (erroDeConexao) {
    mensagemSuspensao.value = 'Não foi possível conectar ao servidor.'
  }
}

function editarSuspensao(suspensao) {
  editandoSuspensaoId.value = suspensao.id_suspensao
  idSemestreSuspensao.value = suspensao.id_semestre
  motivoSuspensao.value = suspensao.motivo
  dataInicioSuspensao.value = suspensao.data_inicio_suspensao
  dataFimSuspensao.value = suspensao.data_fim_suspensao
}

function cancelarEdicaoSuspensao() {
  editandoSuspensaoId.value = null
  idSemestreSuspensao.value = ''
  motivoSuspensao.value = ''
  dataInicioSuspensao.value = ''
  dataFimSuspensao.value = ''
}

async function buscarSuspensoes() {
  try {
    const resposta = await fetch('http://localhost:8000/configuracoes/suspensoes', {
      headers: {
        Authorization: `Bearer ${authStore.token}`,
      },
    })

    if (!resposta.ok) {
      console.log('Rota de suspensões ainda não existe ou deu erro')
      return
    }

    const dados = await resposta.json()
    suspensoes.value = dados
  } catch (erro) {
    console.log('Erro ao buscar suspensões')
  }
}

async function buscarSemestres() {
  try {
    const resposta = await fetch('http://localhost:8000/configuracoes/semestres', {
      headers: {
        Authorization: `Bearer ${authStore.token}`,
      },
    })

    if (!resposta.ok) {
      console.log('Rota de semestres ainda não existe ou deu erro')
      return
    }

    const dados = await resposta.json()
    semestres.value = dados
  } catch (erro) {
    console.log('Erro ao buscar semestres')
  }
}

async function deletarSuspensao(id) {
  const confirmar = confirm('Tem certeza que deseja excluir essa suspensão?')
  if (!confirmar) return

  try {
    const resposta = await fetch(`http://localhost:8000/configuracoes/suspensoes/${id}`, {
      method: 'DELETE',
      headers: {
        Authorization: `Bearer ${authStore.token}`,
      },
    })

    if (!resposta.ok) {
      mensagemSuspensao.value = 'Erro ao excluir suspensão.'
      return
    }

    buscarSuspensoes()
  } catch (erro) {
    mensagemSuspensao.value = 'Não foi possível conectar ao servidor.'
  }
}

onMounted(() => {
  buscarSemestres()
  buscarSuspensoes()
})
</script>

<template>
  <DefaultLayout>
    <div class="page-header">
      <h1>Suspensões de Calendário</h1>
    </div>

    <div class="form-card">
      <h2>{{ editandoSuspensaoId ? 'Editar Suspensão' : 'Cadastrar Suspensão' }}</h2>
      
      <form @submit.prevent="cadastrarSuspensao">
        <div class="form-grid">
          <div class="form-group">
            <label>Semestre</label>
            <select class="form-control" v-model="idSemestreSuspensao" required>
              <option value="" disabled>Selecione um semestre</option>
              <option
                v-for="semestre in semestres"
                :key="semestre.id_semestre"
                :value="semestre.id_semestre"
              >
                {{ semestre.codigo_semestre }}
              </option>
            </select>
          </div>

          <div class="form-group">
            <label>Motivo (ex: Greve Docente)</label>
            <input type="text" class="form-control" v-model="motivoSuspensao" required />
          </div>

          <div class="form-group">
            <label>Data de início</label>
            <input type="date" class="form-control" v-model="dataInicioSuspensao" required />
          </div>

          <div class="form-group">
            <label>Data de fim <small>(opcional)</small></label>
            <input type="date" class="form-control" v-model="dataFimSuspensao" />
          </div>
        </div>

        <div class="form-actions">
          <BaseButton type="submit" variant="primary">
            {{ editandoSuspensaoId ? 'Salvar Edição' : 'Cadastrar Suspensão' }}
          </BaseButton>
          
          <BaseButton 
            v-if="editandoSuspensaoId" 
            type="button" 
            variant="secondary" 
            @click="cancelarEdicaoSuspensao">
            Cancelar
          </BaseButton>
        </div>
      </form>
      
      <div v-if="mensagemSuspensao" class="alert alert-info mt-3">
        {{ mensagemSuspensao }}
      </div>
    </div>

    <div class="table-container">
      <h2>Suspensões Cadastradas</h2>
      <table>
        <thead>
          <tr>
            <th>Semestre</th>
            <th>Motivo</th>
            <th>Início</th>
            <th>Fim</th>
            <th class="actions-col">Ações</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="suspensao in suspensoes" :key="suspensao.id_suspensao">
            <td><strong>{{ suspensao.id_semestre }}</strong></td>
            <td>{{ suspensao.motivo }}</td>
            <td>{{ suspensao.data_inicio_suspensao }}</td>
            <td>{{ suspensao.data_fim_suspensao || '-' }}</td>
            <td class="actions-col">
              <div class="action-buttons">
                <BaseButton type="button" variant="secondary" @click="editarSuspensao(suspensao)">
                  Editar
                </BaseButton>
                <BaseButton type="button" variant="danger" @click="deletarSuspensao(suspensao.id_suspensao)">
                  Excluir
                </BaseButton>
              </div>
            </td>
          </tr>
          <tr v-if="suspensoes.length === 0">
            <td colspan="5" class="text-center">Nenhuma suspensão cadastrada.</td>
          </tr>
        </tbody>
      </table>
    </div>
  </DefaultLayout>
</template>

<style scoped>
/* Espaçamentos Globais */
.mt-3 { margin-top: 16px; }
.mt-4 { margin-top: 24px; }
.text-center { text-align: center; }
.text-muted { color: #6b7280; font-style: italic; }

/* Tipografia e Cabeçalhos */
.page-header h1 {
  font-size: 1.8rem;
  color: #111827;
  margin-bottom: 24px;
}
h2 {
  font-size: 1.25rem;
  color: #374151;
  margin-top: 0;
  margin-bottom: 16px;
  border-bottom: 1px solid #e5e7eb;
  padding-bottom: 8px;
}

/* Estilos de Card para Forms e Detalhes */
.form-card, .details-card {
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 24px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.05);
  margin-bottom: 32px;
}

/* Formulários */
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
  transition: border-color 0.2s, box-shadow 0.2s;
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

/* Tabelas Modernas */
.table-container {
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 1px 3px rgba(0,0,0,0.05);
}
.table-container h2 {
  padding: 20px 20px 0 20px;
  border-bottom: none;
  margin-bottom: 8px;
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
  border-bottom: 1px solid #e5e7eb;
  font-size: 0.875rem;
}
td {
  padding: 14px 20px;
  border-bottom: 1px solid #e5e7eb;
  color: #4b5563;
  font-size: 0.95rem;
}
tbody tr {
  cursor: default;
  transition: background-color 0.15s;
}
tbody tr:hover td {
  background-color: #f9fafb;
}
tbody tr:last-child td {
  border-bottom: none;
}

/* Alertas */
.alert {
  padding: 12px 16px;
  border-radius: 6px;
  font-size: 0.95rem;
}
.alert-info {
  background-color: #eff6ff;
  color: #1e40af;
  border: 1px solid #bfdbfe;
}

/* ESPECÍFICO DE SUSPENSÕES */
.action-buttons {
  display: flex;
  gap: 8px;
  justify-content: flex-end;
}
.actions-col {
  width: 180px;
}
small {
  color: #6b7280;
  font-weight: 400;
}
</style>