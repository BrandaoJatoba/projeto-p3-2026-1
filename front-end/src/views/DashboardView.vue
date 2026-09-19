<script setup>
import DefaultLayout from '../layouts/DefaultLayout.vue'
import { ref } from 'vue'

// Exemplo de métricas para ilustrar o painel
const resumos = ref([
  { titulo: 'Alunos Ativos', valor: '38', cor: 'text-blue-600' },
  { titulo: 'Qualificações este Mês', valor: '4', cor: 'text-amber-600' },
  { titulo: 'Defesas Agendadas', valor: '2', cor: 'text-emerald-600' },
  { titulo: 'Prazos Críticos', valor: '5', cor: 'text-rose-600' },
])
</script>

<template>
  <DefaultLayout>
    <!-- Card de Boas-Vindas / Perfil -->
    <div class="mb-8 bg-white p-6 rounded-2xl border border-gray-200 shadow-sm flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
      <div>
        <h2 class="text-2xl font-bold text-gray-900">Painel Principal</h2>
        <p class="text-sm text-gray-500 mt-1">Visão geral do progresso das turmas de mestrado.</p>
      </div>
      
      <span class="px-3 py-1 bg-emerald-100 text-emerald-800 text-xs font-semibold rounded-full">
        Sessão Autenticada
      </span>
    </div>

    <!-- Grid de Métricas -->
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
      <div 
        v-for="(item, index) in resumos" 
        :key="index" 
        class="bg-white p-5 rounded-xl border border-gray-200 shadow-sm"
      >
        <p class="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1">
          {{ item.titulo }}
        </p>
        <p class="text-3xl font-extrabold" :class="item.cor">
          {{ item.valor }}
        </p>
      </div>
    </div>

    <!-- Painel de Conteúdo -->
    <div class="bg-white rounded-2xl border border-gray-200 shadow-sm p-6">
      <h3 class="text-lg font-bold text-gray-900 mb-2">Avisos do Sistema</h3>
      <p class="text-gray-600 text-sm leading-relaxed">
        Esta página é visível apenas para usuários autenticados com as permissões adequadas. Aqui você poderá gerenciar prazos, relatórios semestrais e bancas de defesa.
      </p>
    </div>
  </DefaultLayout>
</template>