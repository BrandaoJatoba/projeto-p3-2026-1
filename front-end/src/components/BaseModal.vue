<script setup>
import { ref, watch, nextTick, onBeforeUnmount } from 'vue'

const props = defineProps({
  aberto: { type: Boolean, default: false },
  titulo: { type: String, required: true },
  larguraMaxima: { type: String, default: '600px' },
})

const emit = defineEmits(['fechar'])

const caixa = ref(null)
const idTitulo = `modal-titulo-${Math.random().toString(36).slice(2)}`
let elementoAnterior = null

function aoTeclar(evento) {
  if (evento.key === 'Escape') emit('fechar')
}

function prepararAbertura() {
  elementoAnterior = document.activeElement
  document.addEventListener('keydown', aoTeclar)
  document.body.style.overflow = 'hidden'
}

function limpar() {
  document.removeEventListener('keydown', aoTeclar)
  document.body.style.overflow = ''
  if (elementoAnterior && typeof elementoAnterior.focus === 'function') {
    elementoAnterior.focus()
  }
  elementoAnterior = null
}

watch(
  () => props.aberto,
  async (aberto, estavaAberto) => {
    if (aberto) {
      prepararAbertura()
      await nextTick()
      const primeiroCampo = caixa.value?.querySelector('input, select, textarea')
      ;(primeiroCampo || caixa.value)?.focus()
    } else if (estavaAberto) {
      limpar()
    }
  },
  { immediate: true },
)

onBeforeUnmount(() => {
  if (props.aberto) limpar()
})
</script>

<template>
  <Teleport to="body">
    <div v-if="aberto" class="modal-overlay" @click.self="emit('fechar')">
      <div
        ref="caixa"
        class="modal-container"
        role="dialog"
        aria-modal="true"
        :aria-labelledby="idTitulo"
        tabindex="-1"
        :style="{ maxWidth: larguraMaxima }"
      >
        <div class="modal-header">
          <h2 :id="idTitulo">{{ titulo }}</h2>
          <button type="button" class="botao-fechar" aria-label="Fechar" @click="emit('fechar')">
            &times;
          </button>
        </div>

        <div class="modal-body">
          <slot />
        </div>

        <div v-if="$slots.rodape" class="modal-footer">
          <slot name="rodape" />
        </div>
      </div>
    </div>
  </Teleport>
</template>

<style scoped>
.modal-overlay {
  position: fixed;
  inset: 0;
  z-index: 100;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 16px;
  background-color: rgba(17, 24, 39, 0.5);
}

.modal-container {
  display: flex;
  flex-direction: column;
  width: 100%;
  max-height: calc(100vh - 32px);
  background-color: #ffffff;
  border-radius: 8px;
  box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.modal-container:focus {
  outline: none;
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 24px;
  border-bottom: 1px solid #e5e7eb;
}

.modal-header h2 {
  margin: 0;
  font-size: 1.25rem;
  font-weight: 600;
  color: #111827;
}

.botao-fechar {
  padding: 0 4px;
  border: none;
  border-radius: 4px;
  background: none;
  font-size: 1.5rem;
  line-height: 1;
  color: #6b7280;
  cursor: pointer;
}

.botao-fechar:hover {
  color: #111827;
}

.botao-fechar:focus-visible {
  outline: 2px solid #3b82f6;
  outline-offset: 2px;
}

.modal-body {
  padding: 24px;
  overflow-y: auto;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 16px 24px;
  border-top: 1px solid #e5e7eb;
}
</style>
