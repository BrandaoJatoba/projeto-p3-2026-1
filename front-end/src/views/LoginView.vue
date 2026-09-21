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
    router.push('/dashboard')
  } catch (erroDeConexao) {
    erro.value = 'Não foi possível conectar ao servidor. Tente novamente.'
  }
}
</script>

<template>
  <div class="min-h-screen bg-gray-100 flex items-center justify-center p-4">
    <!-- Box do Formulário de Login -->
    <div class="w-full max-w-md bg-white rounded-2xl shadow-xl border border-gray-100 p-8">
      
      <!-- Cabeçalho do Card -->
      <div class="text-center mb-8">
        <h1 class="text-2xl font-bold text-gray-900">Acompanhamento PPGI - IC</h1>
        <p class="text-sm text-gray-500 mt-1">Acesse sua conta para continuar</p>
      </div>

      <!-- Alerta de Erro -->
      <div 
        v-if="erro" 
        class="mb-6 p-4 bg-red-50 border border-red-200 text-red-600 rounded-lg text-sm flex items-center gap-2"
      >
        <span>⚠️</span>
        <span>{{ erro }}</span>
      </div>

      <!-- Formulário -->
      <form @submit.prevent="fazerLogin" class="space-y-5">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">E-mail</label>
          <input 
            type="email" 
            v-model="email" 
            required 
            placeholder="seu.email@ic.ufal.br"
            class="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all text-sm"
          />
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Senha</label>
          <input 
            type="password" 
            v-model="senha" 
            required 
            placeholder="••••••••"
            class="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all text-sm"
          />
        </div>

        <button 
          type="submit" 
          class="w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-2.5 rounded-lg shadow-md hover:shadow-lg transition-all text-sm"
        >
          Entrar
        </button>
      </form>

    </div>
  </div>
</template>

<style scoped></style>
