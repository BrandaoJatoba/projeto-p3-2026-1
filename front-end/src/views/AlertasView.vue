<script setup>
import { ref, computed, onMounted, nextTick } from 'vue'
import { useAuthStore } from '../stores/auth'
import DefaultLayout from '../layouts/DefaultLayout.vue'
import BaseButton from '../components/BaseButton.vue'

const authStore = useAuthStore()
const prazos = ref([])
const erroPrazos = ref(false)
const gatilhosPorPrazo = ref({})
const erroPorPrazo = ref({})
const alterando = ref({})
const aviso = ref(null)
let temporizadorAviso = null

const ehAdmin = computed(() => authStore.usuario?.perfis?.includes('ADMIN') ?? false)

const idTipoPrazoForm = ref('')
const diasForm = ref('')
const mensagemForm = ref('')
const ativoForm = ref(true)
const editandoGatilhoId = ref(null)
const erroForm = ref('')
const salvando = ref(false)

const campoMensagem = ref(null)
const tagsDisponiveis = [
  '{NOME_DISCENTE}',
  '{MATRICULA}',
  '{NOME_PRAZO}',
  '{DATA_LIMITE}',
  '{NOME_ORIENTADOR}',
]

function mostrarAviso(texto, tipo) {
  aviso.value = { texto, tipo }
  clearTimeout(temporizadorAviso)
  temporizadorAviso = setTimeout(() => {
    aviso.value = null
  }, 3000)
}

async function buscarPrazos() {
  try {
    const resposta = await fetch('http://localhost:8000/configuracoes/prazos', {
      headers: { Authorization: `Bearer ${authStore.token}` },
    })

    if (!resposta.ok) {
      erroPrazos.value = true
      return
    }

    prazos.value = await resposta.json()
  } catch (erro) {
    erroPrazos.value = true
  }
}

async function buscarGatilhos(idTipoPrazo) {
  try {
    const resposta = await fetch(
      `http://localhost:8000/configuracoes/gatilhos?id_tipo_prazo=${idTipoPrazo}`,
      { headers: { Authorization: `Bearer ${authStore.token}` } },
    )

    if (!resposta.ok) {
      erroPorPrazo.value[idTipoPrazo] = true
      return
    }

    const gatilhos = await resposta.json()
    gatilhos.sort((a, b) => b.dias_antecedencia - a.dias_antecedencia)
    gatilhosPorPrazo.value[idTipoPrazo] = gatilhos
    erroPorPrazo.value[idTipoPrazo] = false
  } catch (erro) {
    erroPorPrazo.value[idTipoPrazo] = true
  }
}

async function carregarTudo() {
  await buscarPrazos()
  for (const prazo of prazos.value) {
    await buscarGatilhos(prazo.id_tipo_prazo)
  }
}

async function alternarAtivo(gatilho) {
  alterando.value[gatilho.id_gatilho] = true

  try {
    const resposta = await fetch(
      `http://localhost:8000/configuracoes/gatilhos/${gatilho.id_gatilho}`,
      {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${authStore.token}`,
        },
        body: JSON.stringify({ ativo: !gatilho.ativo }),
      },
    )

    if (!resposta.ok) {
      mostrarAviso('Não foi possível alterar o estado do gatilho.', 'erro')
      return
    }

    Object.assign(gatilho, await resposta.json())
    mostrarAviso(gatilho.ativo ? 'Gatilho ativado.' : 'Gatilho desativado.', 'sucesso')
  } catch (erro) {
    mostrarAviso('Não foi possível conectar ao servidor.', 'erro')
  } finally {
    alterando.value[gatilho.id_gatilho] = false
  }
}

async function excluirGatilho(gatilho) {
  const confirmar = confirm(
    `Excluir o gatilho de ${gatilho.dias_antecedencia} dias? Essa ação não pode ser desfeita.`,
  )
  if (!confirmar) return

  alterando.value[gatilho.id_gatilho] = true

  try {
    const resposta = await fetch(
      `http://localhost:8000/configuracoes/gatilhos/${gatilho.id_gatilho}`,
      {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${authStore.token}` },
      },
    )

    if (resposta.status === 403) {
      mostrarAviso('Apenas administradores podem excluir gatilhos.', 'erro')
      return
    }

    if (!resposta.ok) {
      mostrarAviso('Não foi possível excluir o gatilho.', 'erro')
      return
    }

    if (editandoGatilhoId.value === gatilho.id_gatilho) cancelarEdicao()

    await buscarGatilhos(gatilho.id_tipo_prazo)
    mostrarAviso('Gatilho excluído.', 'sucesso')
  } catch (erro) {
    mostrarAviso('Não foi possível conectar ao servidor.', 'erro')
  } finally {
    alterando.value[gatilho.id_gatilho] = false
  }
}

function validarFormulario() {
  if (!idTipoPrazoForm.value) return 'Escolha o tipo de prazo.'

  if (diasForm.value === '' || diasForm.value === null) {
    return 'Informe os dias de antecedência.'
  }

  const dias = Number(diasForm.value)
  if (!Number.isInteger(dias) || dias < 0) {
    return 'Os dias de antecedência precisam ser um número inteiro maior ou igual a 0.'
  }

  const existentes = gatilhosPorPrazo.value[idTipoPrazoForm.value]
  if (!existentes) {
    return 'Os gatilhos deste prazo não foram carregados, então não dá para conferir se esses dias já existem.'
  }

  const repetido = existentes.some(
    (g) => g.dias_antecedencia === dias && g.id_gatilho !== editandoGatilhoId.value,
  )
  if (repetido) return 'Já existe um gatilho com esse número de dias neste prazo.'

  if (!mensagemForm.value.trim()) return 'Escreva a mensagem do gatilho.'

  return ''
}

function iniciarEdicao(gatilho) {
  editandoGatilhoId.value = gatilho.id_gatilho
  idTipoPrazoForm.value = gatilho.id_tipo_prazo
  diasForm.value = gatilho.dias_antecedencia
  mensagemForm.value = gatilho.mensagem_template || ''
  ativoForm.value = gatilho.ativo
  erroForm.value = ''
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

function cancelarEdicao() {
  editandoGatilhoId.value = null
  idTipoPrazoForm.value = ''
  diasForm.value = ''
  mensagemForm.value = ''
  ativoForm.value = true
  erroForm.value = ''
}

function inserirTag(tag) {
  const campo = campoMensagem.value
  const inicio = campo.selectionStart
  const fim = campo.selectionEnd
  const texto = mensagemForm.value

  mensagemForm.value = texto.slice(0, inicio) + tag + texto.slice(fim)

  nextTick(() => {
    campo.focus()
    const novaPosicao = inicio + tag.length
    campo.setSelectionRange(novaPosicao, novaPosicao)
  })
}

async function salvarGatilho() {
  erroForm.value = validarFormulario()
  if (erroForm.value) return

  salvando.value = true
  const editando = editandoGatilhoId.value !== null
  const idTipoPrazo = idTipoPrazoForm.value

  const corpo = {
    dias_antecedencia: Number(diasForm.value),
    mensagem_template: mensagemForm.value,
    ativo: ativoForm.value,
  }
  if (!editando) corpo.id_tipo_prazo = idTipoPrazo

  const url = editando
    ? `http://localhost:8000/configuracoes/gatilhos/${editandoGatilhoId.value}`
    : 'http://localhost:8000/configuracoes/gatilhos'

  try {
    const resposta = await fetch(url, {
      method: editando ? 'PUT' : 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${authStore.token}`,
      },
      body: JSON.stringify(corpo),
    })

    if (!resposta.ok) {
      erroForm.value = 'Não foi possível salvar o gatilho. Confira os dados.'
      return
    }

    await buscarGatilhos(idTipoPrazo)
    mostrarAviso(editando ? 'Gatilho atualizado.' : 'Gatilho cadastrado.', 'sucesso')
    cancelarEdicao()
  } catch (erro) {
    erroForm.value = 'Não foi possível conectar ao servidor.'
  } finally {
    salvando.value = false
  }
}

onMounted(() => {
  carregarTudo()
})
</script>

<template>
  <DefaultLayout>
    <div
      v-if="aviso"
      class="aviso-flutuante"
      :class="aviso.tipo === 'sucesso' ? 'aviso-sucesso' : 'aviso-erro'"
    >
      {{ aviso.texto }}
    </div>

    <div class="page-header">
      <h1>Réguas e Gatilhos de Alertas</h1>
    </div>

    <div class="form-card">
      <h2>{{ editandoGatilhoId ? 'Editar gatilho' : 'Novo gatilho' }}</h2>

      <form @submit.prevent="salvarGatilho">
        <div class="form-grid">
          <div class="form-group">
            <label>Tipo de prazo</label>
            <select
              class="form-control"
              v-model="idTipoPrazoForm"
              :disabled="editandoGatilhoId !== null"
              required
            >
              <option value="" disabled>Selecione um tipo de prazo</option>
              <option
                v-for="prazo in prazos"
                :key="prazo.id_tipo_prazo"
                :value="prazo.id_tipo_prazo"
              >
                {{ prazo.nome_prazo }}
              </option>
            </select>
          </div>

          <div class="form-group">
            <label>Dias de antecedência</label>
            <input
              type="number"
              min="0"
              step="1"
              class="form-control"
              v-model="diasForm"
              required
            />
          </div>

          <div class="form-group campo-largo">
            <label>Mensagem</label>
            <textarea
              ref="campoMensagem"
              class="form-control"
              rows="4"
              v-model="mensagemForm"
              required
            ></textarea>
            <div class="tags">
              <span class="tags-titulo">Inserir tag:</span>
              <button
                v-for="tag in tagsDisponiveis"
                :key="tag"
                type="button"
                class="tag-btn"
                @mousedown.prevent
                @click="inserirTag(tag)"
              >
                {{ tag }}
              </button>
            </div>
          </div>

          <div class="form-group">
            <label class="campo-check">
              <input type="checkbox" v-model="ativoForm" />
              Gatilho ativo
            </label>
          </div>
        </div>

        <p v-if="erroForm" class="aviso-erro aviso-form">{{ erroForm }}</p>

        <div class="form-actions">
          <BaseButton type="submit" variant="primary" :disabled="salvando">
            {{ editandoGatilhoId ? 'Salvar edição' : 'Cadastrar gatilho' }}
          </BaseButton>
          <BaseButton
            v-if="editandoGatilhoId"
            type="button"
            variant="secondary"
            @click="cancelarEdicao"
          >
            Cancelar
          </BaseButton>
        </div>
      </form>
    </div>

    <p v-if="erroPrazos" class="aviso-erro">Não foi possível carregar os tipos de prazo.</p>
    <p v-else-if="prazos.length === 0" class="aviso-vazio">Nenhum tipo de prazo cadastrado.</p>

    <div v-for="prazo in prazos" :key="prazo.id_tipo_prazo" class="prazo-card">
      <div class="prazo-header">
        <h2>{{ prazo.nome_prazo }}</h2>
        <span class="prazo-codigo">
          {{ prazo.codigo_prazo }}
          <template v-if="gatilhosPorPrazo[prazo.id_tipo_prazo]">
            · {{ gatilhosPorPrazo[prazo.id_tipo_prazo].length }} gatilhos
          </template>
        </span>
        <p class="prazo-descricao">{{ prazo.descricao }}</p>
      </div>

      <div v-if="erroPorPrazo[prazo.id_tipo_prazo]" class="prazo-aviso">
        <p class="aviso-erro">Não foi possível carregar os gatilhos deste prazo.</p>
      </div>
      <div v-else-if="!gatilhosPorPrazo[prazo.id_tipo_prazo]" class="prazo-aviso">
        <p class="aviso-vazio">Carregando gatilhos...</p>
      </div>
      <div v-else-if="gatilhosPorPrazo[prazo.id_tipo_prazo].length === 0" class="prazo-aviso">
        <p class="aviso-vazio">Nenhum gatilho cadastrado para este prazo.</p>
      </div>
      <table v-else>
        <thead>
          <tr>
            <th>Antecedência</th>
            <th>Mensagem</th>
            <th>Estado</th>
            <th class="coluna-acoes">Ações</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="gatilho in gatilhosPorPrazo[prazo.id_tipo_prazo]" :key="gatilho.id_gatilho">
            <td>{{ gatilho.dias_antecedencia }} dias</td>
            <td>{{ gatilho.mensagem_template || '-' }}</td>
            <td>
              <span class="badge" :class="gatilho.ativo ? 'badge-ativo' : 'badge-inativo'">
                {{ gatilho.ativo ? 'Ativo' : 'Inativo' }}
              </span>
            </td>
            <td class="coluna-acoes">
              <div class="acoes">
                <BaseButton type="button" variant="secondary" @click="iniciarEdicao(gatilho)">
                  Editar
                </BaseButton>
                <BaseButton
                  type="button"
                  variant="secondary"
                  :disabled="alterando[gatilho.id_gatilho]"
                  @click="alternarAtivo(gatilho)"
                >
                  {{ gatilho.ativo ? 'Desativar' : 'Ativar' }}
                </BaseButton>
                <BaseButton
                  v-if="ehAdmin"
                  type="button"
                  variant="danger"
                  :disabled="alterando[gatilho.id_gatilho]"
                  @click="excluirGatilho(gatilho)"
                >
                  Excluir
                </BaseButton>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </DefaultLayout>
</template>

<style scoped>
.page-header h1 {
  font-size: 1.8rem;
  color: #111827;
  margin-bottom: 24px;
}

.form-card {
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 24px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  margin-bottom: 32px;
}
.form-card h2 {
  font-size: 1.25rem;
  color: #374151;
  margin: 0 0 16px 0;
  border-bottom: 1px solid #e5e7eb;
  padding-bottom: 8px;
}
.form-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
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
  color: #4b5563;
}
.form-control {
  padding: 10px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 1rem;
  font-family: inherit;
  transition:
    border-color 0.2s,
    box-shadow 0.2s;
}
.form-control:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}
textarea.form-control {
  resize: vertical;
}
.campo-largo {
  grid-column: 1 / -1;
}
.campo-check {
  display: flex;
  align-items: center;
  gap: 8px;
}
.form-actions {
  display: flex;
  gap: 12px;
  margin-top: 24px;
}
.aviso-form {
  margin-top: 16px;
}

.tags {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  margin-top: 8px;
}
.tags-titulo {
  font-size: 0.8rem;
  color: #6b7280;
}
.tag-btn {
  padding: 4px 10px;
  border: 1px solid #d1d5db;
  border-radius: 999px;
  background: #f9fafb;
  color: #374151;
  font-size: 0.8rem;
  font-family: monospace;
  cursor: pointer;
}
.tag-btn:hover {
  background: #eff6ff;
  border-color: #93c5fd;
}

.prazo-card {
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
  margin-bottom: 24px;
  overflow: hidden;
}
.prazo-header {
  padding: 20px 20px 12px 20px;
}
.prazo-header h2 {
  font-size: 1.25rem;
  color: #374151;
  margin: 0 0 4px 0;
}
.prazo-codigo {
  font-size: 0.8rem;
  color: #6b7280;
}
.prazo-descricao {
  font-size: 0.9rem;
  color: #4b5563;
  margin: 8px 0 0 0;
}
.prazo-aviso {
  padding: 0 20px 20px 20px;
}

.aviso-erro {
  padding: 12px 16px;
  background-color: #fef2f2;
  color: #b91c1c;
  border: 1px solid #fecaca;
  border-radius: 6px;
  font-size: 0.95rem;
  margin: 0;
}
.aviso-sucesso {
  padding: 12px 16px;
  background-color: #ecfdf5;
  color: #065f46;
  border: 1px solid #a7f3d0;
  border-radius: 6px;
  font-size: 0.95rem;
  margin: 0;
}
.aviso-flutuante {
  position: fixed;
  top: 80px;
  right: 24px;
  z-index: 50;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}
.aviso-vazio {
  color: #6b7280;
  font-style: italic;
  margin: 0;
}

table {
  width: 100%;
  border-collapse: collapse;
}
th {
  background-color: #f9fafb;
  color: #374151;
  font-weight: 600;
  text-align: left;
  padding: 12px 20px;
  border-top: 1px solid #e5e7eb;
  border-bottom: 1px solid #e5e7eb;
  font-size: 0.875rem;
}
td {
  padding: 14px 20px;
  border-bottom: 1px solid #e5e7eb;
  color: #4b5563;
  font-size: 0.95rem;
}
tbody tr:last-child td {
  border-bottom: none;
}
.coluna-acoes {
  text-align: right;
  width: 330px;
}
.acoes {
  display: flex;
  gap: 8px;
  justify-content: flex-end;
}

.badge {
  display: inline-block;
  padding: 2px 10px;
  border-radius: 999px;
  font-size: 0.8rem;
  font-weight: 500;
}
.badge-ativo {
  background-color: #ecfdf5;
  color: #065f46;
}
.badge-inativo {
  background-color: #f3f4f6;
  color: #4b5563;
}
</style>
