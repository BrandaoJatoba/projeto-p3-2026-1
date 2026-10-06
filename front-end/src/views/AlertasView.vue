<script setup>
import { ref, onMounted } from 'vue'
import { useAuthStore } from '../stores/auth'
import DefaultLayout from '../layouts/DefaultLayout.vue'

const authStore = useAuthStore()
const prazos = ref([])
const gatilhosPorPrazo = ref({})

async function buscarPrazos() {
  try {
    const resposta = await fetch('http://localhost:8000/configuracoes/prazos', {
      headers: { Authorization: `Bearer ${authStore.token}` },
    })

    if (!resposta.ok) {
      console.log('Erro ao buscar prazos')
      return
    }

    prazos.value = await resposta.json()
  } catch (erro) {
    console.log('Não foi possível conectar ao servidor')
  }
}

async function buscarGatilhos(idTipoPrazo) {
  try {
    const resposta = await fetch(
      `http://localhost:8000/configuracoes/gatilhos?id_tipo_prazo=${idTipoPrazo}`,
      { headers: { Authorization: `Bearer ${authStore.token}` } },
    )

    if (!resposta.ok) {
      console.log('Erro ao buscar gatilhos do prazo', idTipoPrazo)
      return
    }

    gatilhosPorPrazo.value[idTipoPrazo] = await resposta.json()
  } catch (erro) {
    console.log('Não foi possível conectar ao servidor')
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
    <h1>Réguas e Gatilhos de Alertas</h1>
    <p v-for="prazo in prazos" :key="prazo.id_tipo_prazo">
      {{ prazo.nome_prazo }}: {{ gatilhosPorPrazo[prazo.id_tipo_prazo]?.length ?? 0 }} gatilhos
    </p>
  </DefaultLayout>
</template>

<style scoped></style>
