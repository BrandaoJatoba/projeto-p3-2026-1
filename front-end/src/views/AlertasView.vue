<script setup>
import { ref, onMounted } from 'vue'
import { useAuthStore } from '../stores/auth'
import DefaultLayout from '../layouts/DefaultLayout.vue'

const authStore = useAuthStore()
const prazos = ref([])
const erroPrazos = ref(false)
const gatilhosPorPrazo = ref({})
const erroPorPrazo = ref({})

async function buscarPrazos() {
  try {
    const resposta = await fetch('http://localhost:8000/configuracoes/prazos', {
      headers: { Authorization: `Bearer ${authStore.token}` },
    })

    if (!resposta.ok) {
      erroPrazos.value = true
      return
    }

    prazos.value = await resposta.json()
  } catch (erro) {
    erroPrazos.value = true
  }
}

async function buscarGatilhos(idTipoPrazo) {
  try {
    const resposta = await fetch(
      `http://localhost:8000/configuracoes/gatilhos?id_tipo_prazo=${idTipoPrazo}`,
      { headers: { Authorization: `Bearer ${authStore.token}` } },
    )

    if (!resposta.ok) {
      erroPorPrazo.value[idTipoPrazo] = true
      return
    }

    const gatilhos = await resposta.json()
    gatilhos.sort((a, b) => b.dias_antecedencia - a.dias_antecedencia)
    gatilhosPorPrazo.value[idTipoPrazo] = gatilhos
    erroPorPrazo.value[idTipoPrazo] = false
  } catch (erro) {
    erroPorPrazo.value[idTipoPrazo] = true
  }
}

async function carregarTudo() {
  await buscarPrazos()
  for (const prazo of prazos.value) {
    await buscarGatilhos(prazo.id_tipo_prazo)
  }
}

onMounted(() => {
  carregarTudo()
})
</script>

<template>
  <DefaultLayout>
    <div class="page-header">
      <h1>Réguas e Gatilhos de Alertas</h1>
    </div>

    <p v-if="erroPrazos" class="aviso-erro">Não foi possível carregar os tipos de prazo.</p>
    <p v-else-if="prazos.length === 0" class="aviso-vazio">Nenhum tipo de prazo cadastrado.</p>

    <div v-for="prazo in prazos" :key="prazo.id_tipo_prazo" class="prazo-card">
      <div class="prazo-header">
        <h2>{{ prazo.nome_prazo }}</h2>
        <span class="prazo-codigo">
          {{ prazo.codigo_prazo }}
          <template v-if="gatilhosPorPrazo[prazo.id_tipo_prazo]">
            · {{ gatilhosPorPrazo[prazo.id_tipo_prazo].length }} gatilhos
          </template>
        </span>
        <p class="prazo-descricao">{{ prazo.descricao }}</p>
      </div>

      <div v-if="erroPorPrazo[prazo.id_tipo_prazo]" class="prazo-aviso">
        <p class="aviso-erro">Não foi possível carregar os gatilhos deste prazo.</p>
      </div>
      <div v-else-if="!gatilhosPorPrazo[prazo.id_tipo_prazo]" class="prazo-aviso">
        <p class="aviso-vazio">Carregando gatilhos...</p>
      </div>
      <div v-else-if="gatilhosPorPrazo[prazo.id_tipo_prazo].length === 0" class="prazo-aviso">
        <p class="aviso-vazio">Nenhum gatilho cadastrado para este prazo.</p>
      </div>
      <table v-else>
        <thead>
          <tr>
            <th>Antecedência</th>
            <th>Mensagem</th>
            <th>Estado</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="gatilho in gatilhosPorPrazo[prazo.id_tipo_prazo]" :key="gatilho.id_gatilho">
            <td>{{ gatilho.dias_antecedencia }} dias</td>
            <td>{{ gatilho.mensagem_template || '-' }}</td>
            <td>
              <span class="badge" :class="gatilho.ativo ? 'badge-ativo' : 'badge-inativo'">
                {{ gatilho.ativo ? 'Ativo' : 'Inativo' }}
              </span>
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

.prazo-card {
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  margin-bottom: 24px;
  overflow: hidden;
}
.prazo-header {
  padding: 20px 20px 12px 20px;
}
.prazo-header h2 {
  font-size: 1.25rem;
  color: #374151;
  margin: 0 0 4px 0;
}
.prazo-codigo {
  font-size: 0.8rem;
  color: #6b7280;
}
.prazo-descricao {
  font-size: 0.9rem;
  color: #4b5563;
  margin: 8px 0 0 0;
}
.prazo-aviso {
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

.badge {
  display: inline-block;
  padding: 2px 10px;
  border-radius: 999px;
  font-size: 0.8rem;
  font-weight: 500;
}
.badge-ativo {
  background-color: #ecfdf5;
  color: #065f46;
}
.badge-inativo {
  background-color: #f3f4f6;
  color: #4b5563;
}
</style>
