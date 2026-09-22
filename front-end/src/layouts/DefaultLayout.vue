<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const authStore = useAuthStore()
const isLoggingOut = ref(false)

// Estado reativo para abrir/fechar o dropdown de Configurações
const isConfigOpen = ref(false)

const toggleConfig = () => {
  isConfigOpen.value = !isConfigOpen.value
}

const handleLogout = async () => {
  isLoggingOut.value = true
  
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
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    localStorage.removeItem('usuario')
    
    authStore.clear()

    router.push('/login')
    isLoggingOut.value = false
  }
}
</script>

<template>
  <div class="min-h-screen bg-gray-50 flex">
    <!-- Menu Lateral (Sidebar) -->
    <aside class="w-64 bg-white border-r border-gray-200 flex flex-col justify-between hidden md:flex">
      <div class="p-6">
        <h2 class="text-xl font-bold text-blue-900 tracking-wide">
          PPGI - IC
        </h2>
        <p class="text-xs text-gray-500 mt-1">Acompanhamento de Mestrado</p>

        <!-- Navegação do Menu -->
        <nav class="mt-8 space-y-1">
          <!-- Item Principal: Dashboard -->
          <router-link 
            to="/dashboard"
            class="flex items-center gap-2 px-3 py-2 text-sm font-medium text-gray-700 rounded-md hover:bg-gray-100 hover:text-blue-900 transition-colors"
            active-class="bg-blue-50 text-blue-900 font-semibold"
          >
            <!-- Ícone de Quadrados/Grid (Dashboard) -->
            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z" />
            </svg>
            <span>Dashboard</span>
          </router-link>

          <!-- Item Principal: Configurações (Dropdown) -->
          <div>
            <button 
              @click="toggleConfig"
              class="w-full flex items-center justify-between px-3 py-2 text-sm font-medium text-gray-700 rounded-md hover:bg-gray-100 hover:text-blue-900 transition-colors"
            >
              <div class="flex items-center gap-2">
                <!-- Ícone de Engrenagem -->
                <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                </svg>
                <span>Configurações</span>
              </div>
              
              <!-- Seta do Dropdown -->
              <svg 
                xmlns="http://www.w3.org/2000/svg" 
                class="h-4 w-4 text-gray-400 transition-transform duration-200"
                :class="{ 'rotate-180': isConfigOpen }"
                fill="none" 
                viewBox="0 0 24 24" 
                stroke="currentColor"
              >
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
              </svg>
            </button>

            <!-- Opções do Submenu -->
            <div v-show="isConfigOpen" class="mt-1 pl-8 space-y-1">
              <router-link 
                to="/semestres" 
                class="block px-3 py-1.5 text-xs font-medium text-gray-600 rounded-md hover:bg-gray-100 hover:text-blue-900 transition-colors"
                active-class="bg-blue-50 text-blue-900 font-semibold"
              >
                Semestres
              </router-link>
              
              <router-link 
                to="/suspensoes" 
                class="block px-3 py-1.5 text-xs font-medium text-gray-600 rounded-md hover:bg-gray-100 hover:text-blue-900 transition-colors"
                active-class="bg-blue-50 text-blue-900 font-semibold"
              >
                Suspensoes
              </router-link>

              <router-link 
                to="/alertas" 
                class="block px-3 py-1.5 text-xs font-medium text-gray-600 rounded-md hover:bg-gray-100 hover:text-blue-900 transition-colors"
                active-class="bg-blue-50 text-blue-900 font-semibold"
              >
                Alertas
              </router-link>
            </div>
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
        
        <div class="flex items-center gap-4">
          <span class="text-sm text-gray-600">Usuário Conectado</span>
          
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