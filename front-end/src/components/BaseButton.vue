<!-- src/components/BaseButton.vue -->
<template>
  <button :class="['base-button', variant]" v-bind="$attrs">
    <slot></slot>
  </button>
</template>

<script setup>
defineProps({
  variant: {
    type: String,
    default: 'primary' // Opções: 'primary', 'secondary', 'danger'
  }
})
</script>

<style scoped>
.base-button {
  padding: 8px 16px;
  border-radius: 6px;
  font-weight: 500;
  font-size: 0.9rem;
  cursor: pointer;
  border: 1px solid transparent;
  transition: all 0.2s ease-in-out;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.primary {
  background-color: #3b82f6;
  color: white;
}
.primary:hover { background-color: #2563eb; }

.secondary {
  background-color: #f3f4f6;
  color: #374151;
  border-color: #d1d5db;
}
.secondary:hover { background-color: #e5e7eb; }

.danger {
  background-color: #ef4444;
  color: white;
}
.danger:hover { background-color: #dc2626; }
</style>