<script setup>
import { ref, onMounted } from 'vue'
import { useAuthStore } from '../stores/auth'
import DefaultLayout from '../layouts/DefaultLayout.vue'

const authStore = useAuthStore()
const prazos = ref([])

async function buscarPrazos() {
  try {
    const resposta = await fetch('http://localhost:8000/configuracoes/prazos', {
      headers: {
        Authorization: `Bearer ${authStore.token}`,
      },
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

onMounted(() => {
  buscarPrazos()
})
</script>

<template>
  <DefaultLayout>
    <h1>Réguas e Gatilhos de Alertas</h1>
    <p>{{ prazos.length }} tipos de prazo carregados</p>
  </DefaultLayout>
</template>

<style scoped></style>
