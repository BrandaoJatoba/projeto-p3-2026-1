<script setup>
import DefaultLayout from '../layouts/DefaultLayout.vue'
</script>

<template>
  <DefaultLayout>
    <h1>Configurações</h1>
    <p>Selecione uma das opções abaixo para gerenciar:</p>

    <ul>
      <li><RouterLink to="/semestres">Semestres Letivos</RouterLink></li>
      <li><RouterLink to="/suspensoes">Suspensões de Calendário</RouterLink></li>
    </ul>
  </DefaultLayout>
</template>

<style scoped>
ul {
  list-style: none;
  padding: 0;
}

li {
  margin-bottom: 12px;
}
</style>
