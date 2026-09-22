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
  <div class="min-h-screen bg-gray-50 flex">
    <!-- Menu Lateral (Sidebar) -->
    <aside
      class="w-64 bg-white border-r border-gray-200 flex flex-col justify-between hidden md:flex"
    >
      <div class="p-6">
        <h2 class="text-xl font-bold text-blue-900 tracking-wide">PPGI - IC</h2>
        <p class="text-xs text-gray-500 mt-1">Acompanhamento de Mestrado</p>

        <!-- Navegação (Vazia no momento) -->
        <nav class="mt-8 space-y-2">
          <!-- Seus links do menu entrarão aqui no futuro -->
          <div
            class="p-3 border border-dashed border-gray-300 rounded-lg text-center text-xs text-gray-400"
          >
            Menu em construção...
          </div>
        </nav>
      </div>

      <!-- Rodapé da Sidebar -->
      <div class="p-4 border-t border-gray-100 text-xs text-gray-400 text-center">
        Instituto de Computação
      </div>
    </aside>

    <!-- Conteúdo Principal -->
    <div class="flex-1 flex flex-col">
      <!-- Cabeçalho Superior -->
      <header class="bg-white border-b border-gray-200 h-16 flex items-center justify-between px-6">
        <h1 class="text-lg font-semibold text-gray-800">
          Acompanhamento PPGI - IC
        </h1>
        
        <!-- Área do Usuário / Botão de Sair -->
        <div class="flex items-center gap-4">
          <span class="text-sm text-gray-600">Usuário Conectado</span>
          
          <!-- Botão de Logout -->
          <button 
            @click="handleLogout" 
            :disabled="isLoggingOut"
            class="text-sm px-4 py-2 bg-red-50 text-red-600 font-medium rounded-md hover:bg-red-100 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {{ isLoggingOut ? 'Saindo...' : 'Sair' }}
          </button>
        </div>
      </header>

      <!-- Área Dinâmica da Página -->
      <main class="flex-1 p-6">
        <slot />
      </main>
    </div>
  </div>
</template>
