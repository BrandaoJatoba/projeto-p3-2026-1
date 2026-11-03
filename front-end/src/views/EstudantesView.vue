<script setup>
import { ref, onMounted } from 'vue'
import DefaultLayout from '../layouts/DefaultLayout.vue'
import { useAuthStore } from '../stores/auth'

const authStore = useAuthStore()

const estudantes = ref([])
const total = ref(0)
const carregando = ref(false)
const erro = ref('')

const classesStatus = {
  ATIVO: 'status-ativo',
  TRANCADO: 'status-trancado',
  'PROCESSO DE DESLIGAMENTO': 'status-desligamento',
  DESLIGADO: 'status-desligado',
  'PÓS DEFESA': 'status-pos-defesa',
  TITULADO: 'status-titulado',
}

function classeDoStatus(status) {
  return classesStatus[status] || 'status-desligado'
}

function iniciais(nome) {
  const partes = (nome || '').trim().split(/\s+/).filter(Boolean)
  if (partes.length === 0) return '?'
  const primeira = partes[0][0]
  const ultima = partes.length > 1 ? partes[partes.length - 1][0] : ''
  return (primeira + ultima).toUpperCase()
}

async function buscarEstudantes() {
  carregando.value = true
  erro.value = ''
  try {
    const resposta = await fetch('http://localhost:8000/estudantes', {
      headers: { Authorization: `Bearer ${authStore.token}` },
    })
    if (!resposta.ok) {
      if (resposta.status === 401) {
        erro.value = 'Sua sessão expirou. Saia e entre de novo.'
      } else {
        erro.value = `Não foi possível carregar os estudantes (erro ${resposta.status}).`
      }
      return
    }
    const dados = await resposta.json()
    estudantes.value = dados.itens
    total.value = dados.total
  } catch {
    erro.value = 'Não foi possível conectar ao servidor. Verifique se o backend está ligado.'
  } finally {
    carregando.value = false
  }
}

onMounted(buscarEstudantes)
</script>

<template>
  <DefaultLayout>
    <div class="page-header">
      <h1>Estudantes</h1>
    </div>

    <div v-if="carregando" class="estado">Carregando estudantes...</div>

    <div v-else-if="erro" class="aviso-erro">{{ erro }}</div>

    <div v-else-if="estudantes.length === 0" class="estado">Nenhum estudante cadastrado.</div>

    <div v-else class="tabela-card">
      <p class="contagem">
        {{ total }} {{ total === 1 ? 'estudante encontrado' : 'estudantes encontrados' }}
      </p>
      <table class="tabela">
        <thead>
          <tr>
            <th>Nome</th>
            <th>Matrícula</th>
            <th>Semestre</th>
            <th>Status</th>
            <th>E-mail</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="estudante in estudantes" :key="estudante.id_estudante">
            <td>
              <div class="celula-nome">
                <span class="avatar">{{ iniciais(estudante.nome_discente) }}</span>
                <span>{{ estudante.nome_discente }}</span>
                <span v-if="estudante.eh_bolsista" class="selo-bolsista">Bolsista</span>
              </div>
            </td>
            <td>{{ estudante.matricula }}</td>
            <td>{{ estudante.id_semestre }}</td>
            <td>
              <span class="badge" :class="classeDoStatus(estudante.status_atual)">
                {{ estudante.status_atual }}
              </span>
            </td>
            <td>{{ estudante.email }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </DefaultLayout>
</template>

<style scoped>
.page-header {
  margin-bottom: 24px;
}

.page-header h1 {
  font-size: 1.8rem;
  font-weight: 700;
  color: #111827;
  margin: 0;
}

.estado {
  padding: 24px;
  color: #4b5563;
  background-color: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
}

.aviso-erro {
  padding: 16px;
  color: #b91c1c;
  background-color: #fef2f2;
  border: 1px solid #fecaca;
  border-radius: 8px;
}

.tabela-card {
  background-color: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
  overflow: hidden;
}

.contagem {
  margin: 0;
  padding: 16px 24px;
  font-size: 0.9rem;
  color: #4b5563;
}

.tabela {
  width: 100%;
  border-collapse: collapse;
}

.tabela th {
  text-align: left;
  padding: 12px 24px;
  font-size: 0.85rem;
  font-weight: 600;
  color: #374151;
  background-color: #f9fafb;
  border-bottom: 1px solid #e5e7eb;
}

.tabela td {
  padding: 12px 24px;
  font-size: 0.95rem;
  color: #111827;
  border-bottom: 1px solid #e5e7eb;
}

.tabela tbody tr:last-child td {
  border-bottom: none;
}

.celula-nome {
  display: flex;
  align-items: center;
  gap: 12px;
}

.avatar {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  flex-shrink: 0;
  border-radius: 9999px;
  background-color: #dbeafe;
  color: #1e40af;
  font-size: 0.8rem;
  font-weight: 600;
}

.selo-bolsista {
  padding: 2px 8px;
  border-radius: 9999px;
  border: 1px solid #99f6e4;
  background-color: #f0fdfa;
  color: #115e59;
  font-size: 0.75rem;
  font-weight: 500;
}

.badge {
  display: inline-block;
  padding: 4px 10px;
  border-radius: 9999px;
  font-size: 0.75rem;
  font-weight: 600;
  white-space: nowrap;
}

.status-ativo {
  background-color: #ecfdf5;
  color: #065f46;
}

.status-trancado {
  background-color: #fffbeb;
  color: #92400e;
}

.status-desligamento {
  background-color: #fef2f2;
  color: #b91c1c;
}

.status-desligado {
  background-color: #f3f4f6;
  color: #4b5563;
}

.status-pos-defesa {
  background-color: #eff6ff;
  color: #1e40af;
}

.status-titulado {
  background-color: #f5f3ff;
  color: #5b21b6;
}
</style>
