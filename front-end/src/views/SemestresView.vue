<script setup>
import { ref, onMounted, computed } from 'vue'
import { useAuthStore } from '../stores/auth'
import DefaultLayout from '../layouts/DefaultLayout.vue'
import BaseButton from '../components/BaseButton.vue' // <-- Importando o botão

const codigoSemestre = ref('')
const dataInicioReal = ref('')
const dataFimReal = ref('')
const diasLetivos = ref('')
const mensagem = ref('')
const semestres = ref([])
const editandoSemestreId = ref(null)

const suspensoes = ref([])
const semestreSelecionado = ref(null)

const authStore = useAuthStore()

function selecionarSemestre(semestre) {
  semestreSelecionado.value = semestre
}

const suspensoesDoSemestreSelecionado = computed(() => {
  if (!semestreSelecionado.value) return []
  return suspensoes.value.filter((s) => s.id_semestre === semestreSelecionado.value.id_semestre)
})

const diasLetivosCalculados = computed(() => {
  if (!semestreSelecionado.value) return 0
  const diasSuspensos = suspensoesDoSemestreSelecionado.value.reduce(
    (soma, s) => soma + (s.dias_suspensos || 0),
    0,
  )
  return semestreSelecionado.value.dias_letivos - diasSuspensos
})

async function cadastrarSemestre() {
  mensagem.value = ''

  const dadosSemestre = {
    codigo_semestre: codigoSemestre.value,
    data_inicio_real: dataInicioReal.value,
    data_fim_real: dataFimReal.value,
    dias_letivos: Number(diasLetivos.value),
  }

  const editando = editandoSemestreId.value !== null
  const url = editando
    ? `http://localhost:8000/configuracoes/semestres/${editandoSemestreId.value}`
    : 'http://localhost:8000/configuracoes/semestres'
  const metodo = editando ? 'PUT' : 'POST'

  try {
    const resposta = await fetch(url, {
      method: metodo,
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${authStore.token}`,
      },
      body: JSON.stringify(dadosSemestre),
    })

    if (!resposta.ok) {
      mensagem.value = 'Erro ao salvar semestre. Confira os dados.'
      return
    }

    mensagem.value = editando
      ? 'Semestre atualizado com sucesso!'
      : 'Semestre cadastrado com sucesso!'
    cancelarEdicaoSemestre()
    buscarSemestres()
  } catch (erroDeConexao) {
    mensagem.value = 'Não foi possível conectar ao servidor.'
  }
}

function editarSemestre(semestre) {
  editandoSemestreId.value = semestre.id_semestre
  codigoSemestre.value = semestre.codigo_semestre
  dataInicioReal.value = semestre.data_inicio_real
  dataFimReal.value = semestre.data_fim_real
  diasLetivos.value = semestre.dias_letivos
}

function cancelarEdicaoSemestre() {
  editandoSemestreId.value = null
  codigoSemestre.value = ''
  dataInicioReal.value = ''
  dataFimReal.value = ''
  diasLetivos.value = ''
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

onMounted(() => {
  buscarSemestres()
  buscarSuspensoes()
})
</script>

<template>
  <DefaultLayout>
    <div class="page-header">
      <h1>Semestres Letivos</h1>
    </div>

    <div class="form-card">
      <h2>{{ editandoSemestreId ? 'Editar Semestre' : 'Cadastrar Semestre' }}</h2>
      
      <form @submit.prevent="cadastrarSemestre">
        <div class="form-grid">
          <div class="form-group">
            <label>Código do semestre (ex: 2026.1)</label>
            <input type="text" class="form-control" v-model="codigoSemestre" required />
          </div>

          <div class="form-group">
            <label>Data de início</label>
            <input type="date" class="form-control" v-model="dataInicioReal" required />
          </div>

          <div class="form-group">
            <label>Data de fim</label>
            <input type="date" class="form-control" v-model="dataFimReal" required />
          </div>

          <div class="form-group">
            <label>Dias letivos</label>
            <input type="number" class="form-control" v-model="diasLetivos" required />
          </div>
        </div>

        <div class="form-actions">
          <BaseButton type="submit" variant="primary">
            {{ editandoSemestreId ? 'Salvar Edição' : 'Cadastrar Semestre' }}
          </BaseButton>
          
          <BaseButton 
            v-if="editandoSemestreId" 
            type="button" 
            variant="secondary" 
            @click="cancelarEdicaoSemestre">
            Cancelar
          </BaseButton>
        </div>
      </form>
      
      <div v-if="mensagem" class="alert alert-info mt-3">
        {{ mensagem }}
      </div>
    </div>

    <div class="table-container">
      <h2>Semestres Cadastrados</h2>
      <table>
        <thead>
          <tr>
            <th>Código</th>
            <th>Início</th>
            <th>Fim</th>
            <th>Dias letivos</th>
            <th class="actions-col">Ações</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="semestre in semestres"
            :key="semestre.id_semestre"
            :class="{ linhaSelecionada: semestreSelecionado?.id_semestre === semestre.id_semestre }"
            @click="selecionarSemestre(semestre)"
          >
            <td><strong>{{ semestre.codigo_semestre }}</strong></td>
            <td>{{ semestre.data_inicio_real }}</td>
            <td>{{ semestre.data_fim_real }}</td>
            <td>{{ semestre.dias_letivos }}</td>
            <td class="actions-col">
              <BaseButton type="button" variant="secondary" @click.stop="editarSemestre(semestre)">
                Editar
              </BaseButton>
            </td>
          </tr>
          <tr v-if="semestres.length === 0">
            <td colspan="5" class="text-center">Nenhum semestre cadastrado.</td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Detalhes do Semestre Selecionado -->
    <div v-if="semestreSelecionado" class="details-card mt-4">
      <h3>Detalhes do Semestre: <span class="highlight">{{ semestreSelecionado.codigo_semestre }}</span></h3>
      <p class="summary-text">
        Dias letivos calculados (descontando suspensões): 
        <strong>{{ diasLetivosCalculados }}</strong>
      </p>

      <div class="table-container mt-3" v-if="suspensoesDoSemestreSelecionado.length > 0">
        <table>
          <thead>
            <tr>
              <th>Motivo da Suspensão</th>
              <th>Início</th>
              <th>Fim</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="suspensao in suspensoesDoSemestreSelecionado" :key="suspensao.id_suspensao">
              <td>{{ suspensao.motivo }}</td>
              <td>{{ suspensao.data_inicio_suspensao }}</td>
              <td>{{ suspensao.data_fim_suspensao }}</td>
            </tr>
          </tbody>
        </table>
      </div>
      <p v-else class="text-muted mt-3">Nenhuma suspensão registrada para este semestre.</p>
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
  cursor: pointer;
  transition: background-color 0.15s;
}
tbody tr:hover td {
  background-color: #f9fafb;
}
tbody tr:last-child td {
  border-bottom: none;
}
.linhaSelecionada td {
  background-color: #eff6ff !important;
  color: #1e3a8a;
}
.actions-col {
  width: 100px;
  text-align: right;
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
</style>