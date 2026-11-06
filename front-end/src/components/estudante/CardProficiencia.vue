<script setup>
import { ref, computed, watch } from 'vue'
import BaseButton from '../BaseButton.vue'
import BaseModal from '../BaseModal.vue'
import { useAuthStore } from '../../stores/auth'

const props = defineProps({
  idEstudante: { type: Number, required: true },
})

const emit = defineEmits(['aviso'])

const api = 'http://localhost:8000'
const authStore = useAuthStore()

// Valores iguais aos do backend (back-end/db/enumStatus.py).
const opcoesStatusCertificado = [
  { valor: 'PENDENTE', rotulo: 'Pendente', classe: 'situacao-pendente' },
  { valor: 'ENTREGUE', rotulo: 'Entregue', classe: 'situacao-aprovada' },
  { valor: 'DISPENSA', rotulo: 'Dispensa', classe: 'situacao-dispensa' },
]

const proficiencias = ref([])
const carregando = ref(false)
const erro = ref('')

const modalAberto = ref(false)
const salvando = ref(false)
const erroForm = ref('')
const editandoId = ref(null)
const form = ref({})

const proficienciasOrdenadas = computed(() =>
  [...proficiencias.value].sort((a, b) => b.id_proficiencia - a.id_proficiencia),
)

function cabecalho() {
  return { Authorization: `Bearer ${authStore.token}` }
}

function formatarData(texto) {
  if (!texto) return '—'
  const [ano, mes, dia] = texto.slice(0, 10).split('-')
  if (!ano || !mes || !dia) return texto
  return `${dia}/${mes}/${ano}`
}

function situacao(valor) {
  return (
    opcoesStatusCertificado.find((o) => o.valor === valor) || {
      rotulo: valor || '—',
      classe: 'situacao-dispensa',
    }
  )
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

async function buscarProficiencias() {
  carregando.value = true
  erro.value = ''
  try {
    const resposta = await fetch(`${api}/proficiencia/estudante/${props.idEstudante}`, {
      headers: cabecalho(),
    })
    if (resposta.status === 404) {
      proficiencias.value = []
      return
    }
    if (!resposta.ok) {
      erro.value = 'Não foi possível carregar a proficiência.'
      return
    }
    const dados = await resposta.json()
    // A rota pode devolver uma lista ou um registro só: aceitamos os dois.
    if (Array.isArray(dados)) {
      proficiencias.value = dados
    } else {
      proficiencias.value = dados ? [dados] : []
    }
  } catch {
    erro.value = 'Não foi possível carregar a proficiência.'
  } finally {
    carregando.value = false
  }
}

function abrirModal(proficiencia = null) {
  editandoId.value = proficiencia ? proficiencia.id_proficiencia : null
  form.value = proficiencia
    ? {
        status_certificado: proficiencia.status_certificado || 'PENDENTE',
        data_entrega_certificado: (proficiencia.data_entrega_certificado || '').slice(0, 10),
        consolidada_sigaa: Boolean(proficiencia.consolidada_sigaa),
      }
    : {
        status_certificado: 'PENDENTE',
        data_entrega_certificado: '',
        consolidada_sigaa: false,
      }
  erroForm.value = ''
  modalAberto.value = true
}

function fecharModal() {
  if (salvando.value) return
  modalAberto.value = false
}

async function salvar() {
  if (!form.value.status_certificado) {
    erroForm.value = 'Escolha o status do certificado.'
    return
  }

  const editando = editandoId.value !== null
  const dados = {
    id_estudante: props.idEstudante,
    status_certificado: form.value.status_certificado,
    data_entrega_certificado: form.value.data_entrega_certificado || null,
    consolidada_sigaa: form.value.consolidada_sigaa,
  }
  const url = editando ? `${api}/proficiencia/${editandoId.value}` : `${api}/proficiencia`

  erroForm.value = ''
  salvando.value = true
  try {
    const resposta = await fetch(url, {
      method: editando ? 'PUT' : 'POST',
      headers: { ...cabecalho(), 'Content-Type': 'application/json' },
      body: JSON.stringify(dados),
    })

    if (!resposta.ok) {
      const detalhe = await lerMensagemDeErro(resposta)
      if (resposta.status === 401) {
        erroForm.value = 'Sua sessão expirou. Saia e entre de novo.'
      } else if (resposta.status === 403) {
        erroForm.value = 'Você não tem permissão para registrar proficiência.'
      } else {
        erroForm.value = detalhe || 'Não foi possível salvar. Confira os dados.'
      }
      return
    }

    // Atualiza a tabela na hora com o que a API devolveu.
    let salva = null
    try {
      salva = await resposta.json()
    } catch {
      salva = null
    }
    if (salva && salva.id_proficiencia) {
      proficiencias.value = editando
        ? proficiencias.value.map((p) => (p.id_proficiencia === salva.id_proficiencia ? salva : p))
        : [...proficiencias.value, salva]
    } else {
      buscarProficiencias()
    }

    modalAberto.value = false
    emit('aviso', editando ? 'Proficiência atualizada.' : 'Proficiência registrada.', 'sucesso')
  } catch {
    erroForm.value = 'Não foi possível conectar ao servidor.'
  } finally {
    salvando.value = false
  }
}

watch(() => props.idEstudante, buscarProficiencias, { immediate: true })
</script>

<template>
  <section class="card">
    <div class="card-topo">
      <h2>Proficiência</h2>
      <BaseButton type="button" variant="secondary" @click="abrirModal()">
        Registrar proficiência
      </BaseButton>
    </div>

    <p v-if="carregando" class="texto-vazio">Carregando proficiência...</p>
    <p v-else-if="erro" class="aviso-erro">{{ erro }}</p>
    <p v-else-if="proficiencias.length === 0" class="texto-vazio">
      Nenhuma proficiência registrada.
    </p>
    <div v-else class="tabela-rolagem">
      <table class="tabela-simples">
        <thead>
          <tr>
            <th>Certificado</th>
            <th>Entrega</th>
            <th>SIGAA</th>
            <th class="coluna-acoes"><span class="visualmente-oculto">Ações</span></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="proficiencia in proficienciasOrdenadas" :key="proficiencia.id_proficiencia">
            <td>
              <span class="badge" :class="situacao(proficiencia.status_certificado).classe">
                {{ situacao(proficiencia.status_certificado).rotulo }}
              </span>
            </td>
            <td>{{ formatarData(proficiencia.data_entrega_certificado) }}</td>
            <td>
              <span
                class="badge"
                :class="proficiencia.consolidada_sigaa ? 'situacao-aprovada' : 'situacao-dispensa'"
              >
                {{ proficiencia.consolidada_sigaa ? 'Consolidada' : 'Não consolidada' }}
              </span>
            </td>
            <td class="coluna-acoes">
              <button
                type="button"
                class="botao-tabela"
                aria-label="Editar proficiência"
                @click="abrirModal(proficiencia)"
              >
                Editar
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <BaseModal
      :aberto="modalAberto"
      :titulo="editandoId ? 'Editar proficiência' : 'Registrar proficiência'"
      larguraMaxima="520px"
      @fechar="fecharModal"
    >
      <form id="form-proficiencia" class="form-grid" @submit.prevent="salvar">
        <div class="form-group">
          <label for="proficiencia-status">Status do certificado *</label>
          <select id="proficiencia-status" v-model="form.status_certificado" required>
            <option v-for="o in opcoesStatusCertificado" :key="o.valor" :value="o.valor">
              {{ o.rotulo }}
            </option>
          </select>
        </div>

        <div class="form-group">
          <label for="proficiencia-data">Entrega do certificado</label>
          <input id="proficiencia-data" v-model="form.data_entrega_certificado" type="date" />
        </div>

        <div class="form-group-checkbox span-full">
          <input id="proficiencia-sigaa" v-model="form.consolidada_sigaa" type="checkbox" />
          <label for="proficiencia-sigaa">Consolidada no SIGAA</label>
        </div>

        <p v-if="erroForm" class="aviso-erro span-full">{{ erroForm }}</p>
      </form>

      <template #rodape>
        <BaseButton type="button" variant="secondary" :disabled="salvando" @click="fecharModal">
          Cancelar
        </BaseButton>
        <BaseButton type="submit" form="form-proficiencia" variant="primary" :disabled="salvando">
          {{ salvando ? 'Salvando...' : 'Salvar' }}
        </BaseButton>
      </template>
    </BaseModal>
  </section>
</template>

<style scoped>
.card {
  margin-bottom: 24px;
  padding: 24px;
  background-color: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
}

.card-topo {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 16px;
  padding-bottom: 8px;
  border-bottom: 1px solid #e5e7eb;
}

.card-topo h2 {
  margin: 0;
  font-size: 1.25rem;
  color: #374151;
}

.texto-vazio {
  margin: 0;
  color: #9ca3af;
  font-style: italic;
}

.aviso-erro {
  margin: 0;
  padding: 12px 16px;
  color: #b91c1c;
  background-color: #fef2f2;
  border: 1px solid #fecaca;
  border-radius: 8px;
}

.tabela-rolagem {
  overflow-x: auto;
}

.tabela-simples {
  width: 100%;
  border-collapse: collapse;
}

.tabela-simples th {
  padding: 10px 12px;
  text-align: left;
  font-size: 0.8rem;
  font-weight: 600;
  color: #374151;
  background-color: #f9fafb;
  border-bottom: 1px solid #e5e7eb;
  white-space: nowrap;
}

.tabela-simples td {
  padding: 10px 12px;
  font-size: 0.9rem;
  color: #111827;
  border-bottom: 1px solid #e5e7eb;
  white-space: nowrap;
}

.tabela-simples tbody tr:last-child td {
  border-bottom: none;
}

.coluna-acoes {
  text-align: right;
}

.botao-tabela {
  padding: 4px 10px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  background-color: #ffffff;
  color: #374151;
  font: inherit;
  font-size: 0.8rem;
  cursor: pointer;
}

.botao-tabela:hover {
  background-color: #f9fafb;
  border-color: #9ca3af;
}

.botao-tabela:focus-visible {
  outline: 2px solid #3b82f6;
  outline-offset: 2px;
}

.visualmente-oculto {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}

.badge {
  display: inline-block;
  padding: 4px 10px;
  border-radius: 9999px;
  font-size: 0.75rem;
  font-weight: 600;
  white-space: nowrap;
}

.situacao-aprovada {
  background-color: #ecfdf5;
  color: #065f46;
}

.situacao-pendente {
  background-color: #fffbeb;
  color: #92400e;
}

.situacao-dispensa {
  background-color: #f3f4f6;
  color: #4b5563;
}

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

.form-group-checkbox {
  display: flex;
  align-items: center;
  gap: 8px;
}

.form-group-checkbox label {
  font-size: 0.9rem;
  color: #374151;
  cursor: pointer;
}
</style>
