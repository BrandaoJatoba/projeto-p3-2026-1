<script setup>
import { ref, watch } from 'vue'
import BaseButton from '../BaseButton.vue'
import BaseModal from '../BaseModal.vue'
import { useAuthStore } from '../../stores/auth'

const props = defineProps({
  aberto: { type: Boolean, default: false },
  qualificacao: { type: Object, default: null },
  idDissertacao: { type: Number, default: null },
})

const emit = defineEmits(['fechar', 'salvo'])

const api = 'http://localhost:8000'
const authStore = useAuthStore()

// Valores iguais aos do backend (back-end/db/enumStatus.py).
const opcoesStatus = [
  { valor: 'PENDENTE', rotulo: 'Pendente' },
  { valor: 'ENTREGUE', rotulo: 'Entregue' },
  { valor: 'DISPENSA', rotulo: 'Dispensa' },
  { valor: 'REPROVADO', rotulo: 'Reprovado' },
]
const opcoesRetorno = ['Cadastrou Banca', 'Solicitou Prorrogação']

const form = ref({})
const salvando = ref(false)
const erro = ref('')

function preencherFormulario() {
  const q = props.qualificacao
  form.value = {
    status_qualificacao: q?.status_qualificacao || 'PENDENTE',
    tentativa: q?.tentativa ?? 1,
    prazo_maximo_qualificacao: (q?.prazo_maximo_qualificacao || '').slice(0, 10),
    data_realizacao: (q?.data_realizacao || '').slice(0, 10),
    retorno_qualificacao: q?.retorno_qualificacao || '',
  }
  erro.value = ''
}

watch(
  () => props.aberto,
  (aberto) => {
    if (aberto) preencherFormulario()
  },
  { immediate: true },
)

function fechar() {
  if (salvando.value) return
  emit('fechar')
}

async function lerMensagemDeErro(resposta) {
  try {
    const dados = await resposta.json()
    if (typeof dados.detail === 'string') return dados.detail
  } catch {
    // A resposta não veio em JSON.
  }
  return ''
}

function validar() {
  if (!form.value.prazo_maximo_qualificacao) return 'Informe o prazo máximo da qualificação.'
  if (form.value.tentativa !== '' && form.value.tentativa !== null) {
    const tentativa = Number(form.value.tentativa)
    if (!Number.isInteger(tentativa) || tentativa < 1) {
      return 'A tentativa precisa ser um número inteiro maior que 0.'
    }
  }
  if (!props.qualificacao && !props.idDissertacao) {
    return 'Não foi possível identificar a dissertação deste estudante.'
  }
  return ''
}

async function salvar() {
  erro.value = validar()
  if (erro.value) return

  const editando = Boolean(props.qualificacao)
  const dados = {
    status_qualificacao: form.value.status_qualificacao,
    tentativa:
      form.value.tentativa === '' || form.value.tentativa === null
        ? null
        : Number(form.value.tentativa),
    prazo_maximo_qualificacao: form.value.prazo_maximo_qualificacao,
    data_realizacao: form.value.data_realizacao || null,
    retorno_qualificacao: form.value.retorno_qualificacao || null,
  }
  if (!editando) dados.id_dissertacao = props.idDissertacao

  const url = editando
    ? `${api}/qualificacoes/${props.qualificacao.id_qualificacao}`
    : `${api}/qualificacoes`

  salvando.value = true
  try {
    const resposta = await fetch(url, {
      method: editando ? 'PUT' : 'POST',
      headers: {
        Authorization: `Bearer ${authStore.token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(dados),
    })

    if (!resposta.ok) {
      const detalhe = await lerMensagemDeErro(resposta)
      if (resposta.status === 401) {
        erro.value = 'Sua sessão expirou. Saia e entre de novo.'
      } else if (resposta.status === 403) {
        erro.value = 'Você não tem permissão para atualizar a qualificação.'
      } else {
        erro.value = detalhe || 'Não foi possível salvar. Confira os dados.'
      }
      return
    }

    let salva = null
    try {
      salva = await resposta.json()
    } catch {
      salva = null
    }
    emit('salvo', salva, editando)
  } catch {
    erro.value = 'Não foi possível conectar ao servidor.'
  } finally {
    salvando.value = false
  }
}
</script>

<template>
  <BaseModal
    :aberto="aberto"
    :titulo="qualificacao ? 'Atualizar qualificação' : 'Registrar qualificação'"
    @fechar="fechar"
  >
    <form id="form-qualificacao" class="form-grid" @submit.prevent="salvar">
      <div class="form-group">
        <label for="qualificacao-status">Status *</label>
        <select id="qualificacao-status" v-model="form.status_qualificacao" required>
          <option v-for="o in opcoesStatus" :key="o.valor" :value="o.valor">
            {{ o.rotulo }}
          </option>
        </select>
      </div>

      <div class="form-group">
        <label for="qualificacao-tentativa">Tentativa</label>
        <input
          id="qualificacao-tentativa"
          v-model="form.tentativa"
          type="number"
          min="1"
          step="1"
        />
      </div>

      <div class="form-group">
        <label for="qualificacao-prazo">Prazo máximo *</label>
        <input
          id="qualificacao-prazo"
          v-model="form.prazo_maximo_qualificacao"
          type="date"
          required
        />
      </div>

      <div class="form-group">
        <label for="qualificacao-realizacao">Data de realização</label>
        <input id="qualificacao-realizacao" v-model="form.data_realizacao" type="date" />
      </div>

      <div class="form-group span-full">
        <label for="qualificacao-retorno">Retorno do discente</label>
        <select id="qualificacao-retorno" v-model="form.retorno_qualificacao">
          <option value="">Nenhum</option>
          <option v-for="r in opcoesRetorno" :key="r" :value="r">{{ r }}</option>
        </select>
      </div>

      <p v-if="erro" class="aviso-erro span-full">{{ erro }}</p>
    </form>

    <template #rodape>
      <BaseButton type="button" variant="secondary" :disabled="salvando" @click="fechar">
        Cancelar
      </BaseButton>
      <BaseButton type="submit" form="form-qualificacao" variant="primary" :disabled="salvando">
        {{ salvando ? 'Salvando...' : 'Salvar' }}
      </BaseButton>
    </template>
  </BaseModal>
</template>

<style scoped>
.form-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.span-full {
  grid-column: 1 / -1;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.form-group label {
  font-size: 0.875rem;
  font-weight: 500;
  color: #374151;
}

.form-group input,
.form-group select {
  padding: 10px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 0.95rem;
  font-family: inherit;
}

.form-group input:focus,
.form-group select:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.aviso-erro {
  margin: 0;
  padding: 12px 16px;
  color: #b91c1c;
  background-color: #fef2f2;
  border: 1px solid #fecaca;
  border-radius: 8px;
}
</style>
