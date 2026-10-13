<script setup>
import { ref, onMounted } from 'vue'
import { useAuthStore } from '../stores/auth'
import DefaultLayout from '../layouts/DefaultLayout.vue'

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

async function buscarProfessores() {
  carregando.value = true
  erro.value = false

  if (usarDadosDeExemplo) {
    professores.value = dadosDeExemplo
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

onMounted(() => {
  buscarProfessores()
})
</script>

<template>
  <DefaultLayout>
    <div class="page-header">
      <h1>Professores</h1>
    </div>

    <p v-if="usarDadosDeExemplo" class="aviso-exemplo">
      Dados de exemplo: a API de professores ainda não está conectada.
    </p>

    <div class="tabela-card">
      <div class="tabela-topo">
        <h2>Corpo docente</h2>
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
      <table v-else>
        <thead>
          <tr>
            <th>Nome</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="professor in professores" :key="professor.id_professor">
            <td>{{ professor.nome_professor }}</td>
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

.tabela-card {
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  overflow: hidden;
}
.tabela-topo {
  padding: 20px;
}
.tabela-topo h2 {
  font-size: 1.25rem;
  color: #374151;
  margin: 0;
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
</style>
