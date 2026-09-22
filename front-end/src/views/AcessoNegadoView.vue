<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth' // Ajuste o caminho se necessário

const router = useRouter()
const authStore = useAuthStore() // Instancia a sua store
const isLoggingOut = ref(false)

const handleLogout = async () => {
  isLoggingOut.value = true
  
  // Como você já usa Pinia, pode pegar o token direto da store ou do localstorage
const accessToken = localStorage.getItem('access_token')
const refreshToken = localStorage.getItem('refresh_token')

  try {
    if (accessToken && refreshToken) {
      await fetch('http://localhost:8000/logout', { 
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${accessToken}`
        },
        body: JSON.stringify({
          refresh_token: refreshToken
        })
      })
    }
  } catch (error) {
    console.error('Erro ao revogar o token no servidor:', error)
  } finally {
    // 1. Limpa o armazenamento local
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    localStorage.removeItem('usuario') // Importante limpar o usuário também!
    authStore.clear()
    
    // 2. Limpa o estado da memória (Crucial para o Vue Router bloquear o acesso!)
    authStore.token = null
    authStore.usuario = null
    
    // Obs: Se a sua store tiver uma "action" dedicada para limpar os dados, 
    // você pode simplesmente chamar algo como: authStore.logout()

    // 3. Redireciona para o login
    router.push('/login')
    isLoggingOut.value = false
  }
}
</script>

<template>
  <h1>Acesso Negado</h1>
  <p>Você está logado, mas não tem permissão para acessar essa página.</p>
  <button 
            @click="handleLogout" 
            :disabled="isLoggingOut"
            class="text-sm px-4 py-2 bg-red-50 text-red-600 font-medium rounded-md hover:bg-red-100 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {{ isLoggingOut ? 'Saindo...' : 'Sair' }}
          </button>
</template>

<style scoped></style>
