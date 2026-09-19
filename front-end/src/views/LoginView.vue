<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const email = ref('')
const senha = ref('')
const erro = ref('')

const router = useRouter()
const authStore = useAuthStore()

async function fazerLogin() {
  erro.value = ''

  try {
    const resposta = await fetch('http://localhost:8000/auth/login', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        email: email.value,
        senha: senha.value,
      }),
    })

    const dados = await resposta.json()

    if (!resposta.ok) {
      erro.value = 'E-mail ou senha inválidos'
      return
    }

    authStore.login(dados)
    router.push('/')
  } catch (erroDeConexao) {
    erro.value = 'Não foi possível conectar ao servidor. Tente novamente.'
  }
}
</script>

<template>
  <form @submit.prevent="fazerLogin">
    <label>E-mail</label>
    <input type="email" v-model="email" required />

    <label>Senha</label>
    <input type="password" v-model="senha" required />

    <button type="submit">Entrar</button>
  </form>
  <p v-if="erro">{{ erro }}</p>
</template>

<style scoped></style>
