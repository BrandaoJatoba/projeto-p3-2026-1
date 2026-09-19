<script setup>
import { RouterLink } from 'vue-router'
</script>

<template>
  <div class="min-h-screen bg-gray-50 flex flex-col">
    <!-- Topbar Pública -->
    <header class="bg-white border-b border-gray-200 py-4 px-8">
      <div class="max-w-7xl mx-auto flex justify-between items-center">
        <h1 class="text-xl font-bold text-blue-900">Acompanhamento PPGI - IC</h1>
        <RouterLink 
          to="/login" 
          class="px-4 py-2 text-sm font-medium text-blue-600 hover:text-blue-700 hover:bg-blue-50 rounded-lg transition-colors"
        >
          Entrar no Sistema →
        </RouterLink>
      </div>
    </header>

    <!-- Conteúdo Principal -->
    <main class="flex-1 max-w-4xl mx-auto w-full px-6 flex flex-col items-center justify-center text-center">
      <span class="px-3 py-1 bg-blue-100 text-blue-800 text-xs font-semibold rounded-full mb-4">
        Portal Acadêmico
      </span>
      
      <h2 class="text-4xl font-extrabold text-gray-900 mb-4 tracking-tight">
        Acompanhamento de Mestrado
      </h2>
      
      <p class="text-lg text-gray-600 mb-8 max-w-2xl">
        Bem-vindo à plataforma do Programa de Pós-Graduação em Informática do Instituto de Computação (IC/UFAL).
      </p>

      <div class="flex gap-4">
        <RouterLink 
          to="/login" 
          class="px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-xl shadow-md hover:shadow-lg transition-all text-sm"
        >
          Acessar Minha Conta
        </RouterLink>
      </div>
    </main>
  </div>
</template>