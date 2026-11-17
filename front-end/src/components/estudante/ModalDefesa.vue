<script setup>
import { computed, ref, watch } from 'vue'
import BaseButton from '../BaseButton.vue'
import BaseModal from '../BaseModal.vue'
import { useAuthStore } from '../../stores/auth'

const props = defineProps({
  aberto: { type: Boolean, default: false },
  defesa: { type: Object, default: null },
  idDissertacao: { type: Number, default: null },
})

const emit = defineEmits(['fechar', 'salvo'])

const api = 'http://localhost:8000'
const authStore = useAuthStore()

// Valores iguais aos do backend (back-end/db/enumStatus.py).
const opcoesHomologacao = [
  { valor: 'PENDENTE', rotulo: 'Pendente' },
  { valor: 'SOLICITADA', rotulo: 'Solicitada' },
  { valor: 'APROVADA_COLEGIADO', rotulo: 'Aprovada pelo colegiado' },
]
const opcoesStatusDefesa = [
  { valor: 'PENDENTE', rotulo: 'Pendente' },
  { valor: 'EM_HOMOLOGACAO', rotulo: 'Em homologação' },
  { valor: 'AGUARDANDO_VERSAO_FINAL', rotulo: 'Aguardando versão final' },
  { valor: 'DEFENDIDA', rotulo: 'Defendida' },
  { valor: 'CONCLUIDO', rotulo: 'Concluído' },
  { valor: 'CANCELADO', rotulo: 'Cancelado' },
]
const opcoesConceito = [
  { valor: 'APROVADO', rotulo: 'Aprovado' },
  { valor: 'APROVADO_CONDICIONALMENTE', rotulo: 'Aprovado condicionalmente' },
  { valor: 'REPROVADO', rotulo: 'Reprovado' },
]
const opcoesDiploma = [
  { valor: 'PENDENTE', rotulo: 'Pendente' },
  { valor: 'DOCUMENTACAO_ENVIADA', rotulo: 'Documentação enviada' },
  { valor: 'PROCESSO_ABERTO', rotulo: 'Processo aberto' },
]

const form = ref({})
const salvando = ref(false)
const erro = ref('')

const editando = computed(() => Boolean(props.defesa))

function dataISO(texto) {
  return (texto || '').slice(0, 10)
}

function formatarDataBR(texto) {
  const iso = dataISO(texto)
  if (!iso) return '—'
  const [ano, mes, dia] = iso.split('-')
  return ano && mes && dia ? `${dia}/${mes}/${ano}` : iso
}

function preencherFormulario() {
  const d = props.defesa
  form.value = {
    data_solicitacao_banca: dataISO(d?.data_solicitacao_banca),
    status_homologacao_banca: d?.status_homologacao_banca || 'PENDENTE',
    prazo_maximo_defesa: dataISO(d?.prazo_maximo_defesa),
    data_realizacao: dataISO(d?.data_realizacao),
    status_defesa: d?.status_defesa || 'PENDENTE',
    conceito_defesa: d?.conceito_defesa || '',
    prazo_limite_processo_diploma: dataISO(d?.prazo_limite_processo_diploma),
    status_processo_diploma: d?.status_processo_diploma || 'PENDENTE',
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

function calcularDiferencaDias(dataInicioISO, dataFimISO) {
  const [anoI, mesI, diaI] = dataInicioISO.split('-').map(Number)
  const [anoF, mesF, diaF] = dataFimISO.split('-').map(Number)
  const inicio = new Date(anoI, mesI - 1, diaI)
  const fim = new Date(anoF, mesF - 1, diaF)
  return Math.round((fim - inicio) / (1000 * 60 * 60 * 24))
}

function validar() {
  const f = form.value

  if (!editando.value) {
    if (!props.idDissertacao) {
      return 'Não foi possível identificar a dissertação deste estudante.'
    }
    if (!f.prazo_maximo_defesa) {
      return 'Informe o prazo máximo da defesa.'
    }
  }

  if (f.data_solicitacao_banca && f.data_realizacao) {
    const dias = calcularDiferencaDias(f.data_solicitacao_banca, f.data_realizacao)
    if (dias < 0) {
      return 'A data de realização da defesa não pode ser anterior à data do pedido da banca.'
    }
    if (dias > 30) {
      return 'Conforme o Art. 37, VI do Regimento, a defesa deve ocorrer no máximo 30 dias após o pedido de homologação da banca.'
    }
  }

  return ''
}

async function salvar() {
  erro.value = validar()
  if (erro.value) return

  const f = form.value
  const dados = {
    data_solicitacao_banca: f.data_solicitacao_banca || null,
    status_homologacao_banca: f.status_homologacao_banca,
    data_realizacao: f.data_realizacao || null,
    status_defesa: f.status_defesa,
    conceito_defesa: f.conceito_defesa || null,
    prazo_limite_processo_diploma: f.prazo_limite_processo_diploma || null,
    status_processo_diploma: f.status_processo_diploma,
  }

  if (!editando.value) {
    dados.id_dissertacao = props.idDissertacao
    dados.prazo_maximo_defesa = f.prazo_maximo_defesa
  }

  const url = editando.value ? `${api}/defesas/${props.defesa.id_defesa}` : `${api}/defesas`

  salvando.value = true
  try {
    const resposta = await fetch(url, {
      method: editando.value ? 'PUT' : 'POST',
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
        erro.value = 'Você não tem permissão para atualizar a defesa.'
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
    emit('salvo', salva, editando.value)
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
    :titulo="editando ? 'Atualizar defesa' : 'Registrar defesa'"
    larguraMaxima="720px"
    @fechar="fechar"
  >
    <form id="form-defesa" class="secoes" @submit.prevent="salvar">
      <fieldset class="secao">
        <legend>1. Banca</legend>
        <div class="form-grid">
          <div class="form-group">
            <label for="defesa-data-solicitacao">Data do pedido da banca</label>
            <input id="defesa-data-solicitacao" v-model="form.data_solicitacao_banca" type="date" />
          </div>
          <div class="form-group">
            <label for="defesa-homologacao">Status da homologação</label>
            <select id="defesa-homologacao" v-model="form.status_homologacao_banca">
              <option v-for="o in opcoesHomologacao" :key="o.valor" :value="o.valor">
                {{ o.rotulo }}
              </option>
            </select>
          </div>
        </div>
        <p class="dica">
          A defesa deve ocorrer no máximo 30 dias após a data do pedido de homologação.
        </p>
      </fieldset>

      <fieldset class="secao">
        <legend>2. Defesa</legend>
        <div class="form-grid">
          <div v-if="!editando" class="form-group">
            <label for="defesa-prazo-maximo">Prazo máximo *</label>
            <input
              id="defesa-prazo-maximo"
              v-model="form.prazo_maximo_defesa"
              type="date"
              required
            />
          </div>
          <div class="form-group">
            <label for="defesa-realizacao">Data de realização</label>
            <input id="defesa-realizacao" v-model="form.data_realizacao" type="date" />
          </div>
          <div class="form-group">
            <label for="defesa-status">Status da defesa</label>
            <select id="defesa-status" v-model="form.status_defesa">
              <option v-for="o in opcoesStatusDefesa" :key="o.valor" :value="o.valor">
                {{ o.rotulo }}
              </option>
            </select>
          </div>
          <div class="form-group">
            <label for="defesa-conceito">Conceito</label>
            <select id="defesa-conceito" v-model="form.conceito_defesa">
              <option value="">Sem conceito</option>
              <option v-for="o in opcoesConceito" :key="o.valor" :value="o.valor">
                {{ o.rotulo }}
              </option>
            </select>
          </div>
        </div>
      </fieldset>

      <fieldset class="secao">
        <legend>3. Depois da defesa</legend>
        <div class="form-grid">
          <div v-if="defesa?.prazo_versao_final" class="form-group">
            <label>Prazo da versão final</label>
            <div class="campo-leitura">{{ formatarDataBR(defesa.prazo_versao_final) }}</div>
          </div>
          <div class="form-group">
            <label for="defesa-prazo-diploma">Prazo do processo de diploma</label>
            <input
              id="defesa-prazo-diploma"
              v-model="form.prazo_limite_processo_diploma"
              type="date"
            />
          </div>
          <div class="form-group">
            <label for="defesa-diploma">Status do diploma</label>
            <select id="defesa-diploma" v-model="form.status_processo_diploma">
              <option v-for="o in opcoesDiploma" :key="o.valor" :value="o.valor">
                {{ o.rotulo }}
              </option>
            </select>
          </div>
        </div>
      </fieldset>

      <p v-if="erro" class="aviso-erro">{{ erro }}</p>
    </form>

    <template #rodape>
      <BaseButton type="button" variant="secondary" :disabled="salvando" @click="fechar">
        Cancelar
      </BaseButton>
      <BaseButton type="submit" form="form-defesa" variant="primary" :disabled="salvando">
        {{ salvando ? 'Salvando...' : 'Salvar' }}
      </BaseButton>
    </template>
  </BaseModal>
</template>

<style scoped>
.secoes {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.secao {
  margin: 0;
  padding: 16px;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
}

.secao legend {
  padding: 0 6px;
  font-size: 0.95rem;
  font-weight: 600;
  color: #374151;
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
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

.campo-leitura {
  padding: 10px;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  background-color: #f9fafb;
  color: #374151;
  font-size: 0.95rem;
}

.dica {
  margin: 10px 0 0 0;
  font-size: 0.8rem;
  color: #6b7280;
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