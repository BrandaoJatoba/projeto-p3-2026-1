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
        <h1 class="text-lg font-semibold text-gray-800">Acompanhamento PPGI - IC</h1>

        <!-- Área do Usuário / Botão de Sair (Opcional) -->
        <div class="flex items-center gap-4">
          <span class="text-sm text-gray-600">Usuário Conectado</span>
        </div>
      </header>

      <!-- Área Dinâmica da Página -->
      <main class="flex-1 p-6">
        <slot />
      </main>
    </div>
  </div>
</template>
