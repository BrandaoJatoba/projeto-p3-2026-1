<script setup>
import { ref, computed, watch, nextTick } from 'vue'
import BaseModal from '../BaseModal.vue'
import BaseButton from '../BaseButton.vue'
import { buscarGatilho, gerarPreviewMinutas, dispararIndividual } from '../../services/alertas'

const props = defineProps({
  aberto: { type: Boolean, default: false },
  // Alertas pendentes escolhidos na Central: 1 = modo individual; 2 ou mais = lote.
  alertas: { type: Array, default: () => [] },
})

const emit = defineEmits(['fechar', 'enviado'])

// Mesmo texto que o back usa quando o gatilho não tem modelo (services/minuta_service.py).
const TEMPLATE_PADRAO =
  'Informamos que o prazo de {nome_prazo} tem data limite em {data_limite}. Caso ainda não tenha providenciado, procure seu(sua) orientador(a) e a Secretaria para dar andamento.'

// Botões de variáveis. Os códigos são os aceitos pelo back (uma chave só).
const variaveis = [
  { rotulo: 'Nome do Discente', codigo: '{nome_discente}' },
  { rotulo: 'Data Limite', codigo: '{data_limite}' },
  { rotulo: 'Dias Restantes', codigo: '{dias_restantes}' },
  { rotulo: 'Orientador', codigo: '{orientador}' },
  { rotulo: 'Coorientadores', codigo: '{coorientadores}' },
]

// Conferência simples do formato; a validação completa é feita pelo back.
const EMAIL_SIMPLES = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

const carregando = ref(false)
const erroCarregar = ref('')
const minuta = ref(null) // prévia do back: destinatário, cc, assunto, corpo, avisos
const motivoIgnorado = ref('') // preenchido se o alerta não está mais pendente
const destinatario = ref('')
const assunto = ref('')
const template = ref('') // miolo do e-mail, com variáveis
const ccRemovidos = ref([]) // id_professor que NÃO vão em cópia
const ccExtras = ref([]) // e-mails a mais em cópia
const novoCc = ref('')
const erroCc = ref('')
const atualizandoPrevia = ref(false)
const previaDesatualizada = ref(false)
const enviando = ref(false)
const erroEnvio = ref('')
const campoTexto = ref(null)

let temporizadorPrevia = null
let versaoPrevia = 0

const modoIndividual = computed(() => props.alertas.length === 1)
const alerta = computed(() => props.alertas[0] || null)
const semEmail = computed(() => Boolean(minuta.value) && !minuta.value.destinatario)
const ccOrientadores = computed(() => minuta.value?.destinatarios_cc || [])
const textoVazio = computed(() => !template.value.trim())

const titulo = computed(() =>
  modoIndividual.value
    ? `Revisar e enviar: ${alerta.value?.nome_discente ?? ''}`
    : `Gerar minutas em lote (${props.alertas.length})`,
)

// O "sem e-mail" do discente já aparece em vermelho no campo Para; os outros avisos ficam no quadro amarelo.
const avisosVisiveis = computed(() =>
  (minuta.value?.avisos || []).filter((aviso) => !aviso.startsWith('Discente sem e-mail')),
)

// Texto que explica por que o botão de enviar está desativado ('' = pode enviar).
const motivoBloqueio = computed(() => {
  if (!minuta.value) return ''
  if (semEmail.value) return 'Discente sem e-mail cadastrado: o envio está bloqueado.'
  if (!EMAIL_SIMPLES.test(destinatario.value.trim())) {
    return 'Informe um e-mail de destinatário válido.'
  }
  if (!assunto.value.trim()) return 'Preencha o assunto.'
  if (textoVazio.value) return 'Escreva o texto do e-mail.'
  if (atualizandoPrevia.value || previaDesatualizada.value) return 'Aguarde a prévia atualizar.'
  return ''
})

const podeEnviar = computed(() => Boolean(minuta.value) && !motivoBloqueio.value && !enviando.value)

function papel(orientador) {
  return String(orientador.tipo_orientacao).toUpperCase().startsWith('CO')
    ? 'Coorientador'
    : 'Principal'
}

function ccRemovido(orientador) {
  return ccRemovidos.value.includes(orientador.id_professor)
}

function textoDias(dias) {
  if (dias === 0) return 'vence hoje'
  if (dias === 1) return 'falta 1 dia'
  if (dias < 0) return `vencido há ${Math.abs(dias)} dia${dias === -1 ? '' : 's'}`
  return `faltam ${dias} dias`
}

function limpar() {
  clearTimeout(temporizadorPrevia)
  versaoPrevia += 1 // descarta qualquer prévia que ainda esteja a caminho
  erroCarregar.value = ''
  minuta.value = null
  motivoIgnorado.value = ''
  destinatario.value = ''
  assunto.value = ''
  template.value = ''
  ccRemovidos.value = []
  ccExtras.value = []
  novoCc.value = ''
  erroCc.value = ''
  atualizandoPrevia.value = false
  previaDesatualizada.value = false
  erroEnvio.value = ''
}

async function carregar() {
  limpar()
  if (!modoIndividual.value) return

  carregando.value = true
  try {
    // A prévia e o modelo do texto (com as variáveis) vêm de rotas diferentes.
    const [previa, gatilho] = await Promise.all([
      gerarPreviewMinutas([alerta.value]),
      buscarGatilho(alerta.value.id_gatilho),
    ])

    if (previa.minutas.length === 0) {
      motivoIgnorado.value = previa.ignorados[0]?.motivo || 'Este alerta não está mais pendente.'
      return
    }

    minuta.value = previa.minutas[0]
    destinatario.value = minuta.value.destinatario || ''
    assunto.value = minuta.value.assunto || ''
    template.value = gatilho?.mensagem_template?.trim() || TEMPLATE_PADRAO
  } catch (e) {
    erroCarregar.value = e?.message || 'Não foi possível montar o e-mail.'
  } finally {
    carregando.value = false
  }
}

// Espera 0,6 s sem digitar antes de pedir a prévia nova ao back.
// Com a caixa vazia, não pede nada: o back trocaria o vazio por um texto padrão,
// e a prévia mostraria um e-mail diferente do que está na caixa.
function agendarPrevia() {
  clearTimeout(temporizadorPrevia)
  versaoPrevia += 1 // descarta qualquer prévia antiga que ainda esteja a caminho
  previaDesatualizada.value = true

  if (textoVazio.value) {
    atualizandoPrevia.value = false
    return
  }
  temporizadorPrevia = setTimeout(atualizarPrevia, 600)
}

async function atualizarPrevia() {
  if (!alerta.value || textoVazio.value) return
  const versao = ++versaoPrevia
  atualizandoPrevia.value = true
  erroEnvio.value = ''
  try {
    const previa = await gerarPreviewMinutas([alerta.value], template.value)
    if (versao !== versaoPrevia) return // já existe uma prévia mais nova a caminho
    if (previa.minutas[0]) {
      minuta.value = previa.minutas[0]
      previaDesatualizada.value = false
    } else {
      motivoIgnorado.value = previa.ignorados[0]?.motivo || 'Este alerta não está mais pendente.'
    }
  } catch (e) {
    if (versao === versaoPrevia) {
      erroEnvio.value = e?.message || 'Não foi possível atualizar a prévia.'
    }
  } finally {
    if (versao === versaoPrevia) atualizandoPrevia.value = false
  }
}

// Coloca a variável onde está o cursor (ou no lugar do trecho selecionado).
async function inserirVariavel(codigo) {
  const campo = campoTexto.value
  const texto = template.value
  const inicio = campo ? campo.selectionStart : texto.length
  const fim = campo ? campo.selectionEnd : texto.length

  template.value = texto.slice(0, inicio) + codigo + texto.slice(fim)
  agendarPrevia()

  // Espera o Vue atualizar a caixa de texto e devolve o cursor para depois da variável.
  await nextTick()
  if (campo) {
    const posicao = inicio + codigo.length
    campo.focus()
    campo.setSelectionRange(posicao, posicao)
  }
}

function alternarCc(orientador) {
  const id = orientador.id_professor
  ccRemovidos.value = ccRemovido(orientador)
    ? ccRemovidos.value.filter((item) => item !== id)
    : [...ccRemovidos.value, id]
}

function adicionarCc() {
  erroCc.value = ''
  const email = novoCc.value.trim()
  if (!email) return
  if (!EMAIL_SIMPLES.test(email)) {
    erroCc.value = 'E-mail inválido.'
    return
  }
  const jaExiste = [
    destinatario.value,
    ...ccOrientadores.value.map((o) => o.email),
    ...ccExtras.value,
  ].some((item) => String(item).trim().toLowerCase() === email.toLowerCase())
  if (jaExiste) {
    erroCc.value = 'Esse e-mail já está no envio.'
    return
  }
  ccExtras.value = [...ccExtras.value, email]
  novoCc.value = ''
}

function removerCcExtra(email) {
  ccExtras.value = ccExtras.value.filter((item) => item !== email)
}

async function enviar() {
  if (!podeEnviar.value) return
  enviando.value = true
  erroEnvio.value = ''

  // O corpo vai pronto (a prévia do back): o back não preenche variáveis no envio.
  const dados = {
    id_estudante: alerta.value.id_estudante,
    id_gatilho: alerta.value.id_gatilho,
    assunto: assunto.value.trim(),
    corpo_mensagem: minuta.value.corpo,
  }
  const destino = destinatario.value.trim()
  if (destino.toLowerCase() !== String(minuta.value.destinatario).toLowerCase()) {
    dados.email_destino = destino
  }
  if (ccRemovidos.value.length) dados.ignorar_cc_ids = [...ccRemovidos.value]
  if (ccExtras.value.length) dados.cc_adicionais = [...ccExtras.value]

  try {
    const registro = await dispararIndividual(dados)
    emit('enviado', { registro, nome: alerta.value.nome_discente })
  } catch (e) {
    erroEnvio.value = e?.message || 'Não foi possível enviar o e-mail.'
  } finally {
    enviando.value = false
  }
}

function fechar() {
  if (enviando.value) return
  clearTimeout(temporizadorPrevia)
  emit('fechar')
}

// Sempre que o modal abre, monta o e-mail do zero.
watch(
  () => props.aberto,
  (aberto) => {
    if (aberto) carregar()
    else clearTimeout(temporizadorPrevia)
  },
)
</script>

<template>
  <BaseModal
    :aberto="aberto"
    :titulo="titulo"
    :larguraMaxima="modoIndividual ? '760px' : '560px'"
    @fechar="fechar"
  >
    <!-- ===== Modo em lote (PROVISÓRIO: a próxima etapa monta a edição em lote) ===== -->
    <template v-if="!modoIndividual">
      <p class="text-sm text-gray-600 mb-4">
        O envio em lote entra na próxima etapa. Por enquanto, esta janela mostra só os alunos
        escolhidos.
      </p>
      <ul class="divide-y divide-gray-100 border border-gray-200 rounded-lg">
        <li
          v-for="item in alertas"
          :key="`${item.id_estudante}-${item.id_gatilho}`"
          class="px-4 py-2 text-sm flex flex-wrap justify-between gap-2"
        >
          <span class="font-medium text-gray-900">{{ item.nome_discente }}</span>
          <span class="text-gray-500">
            {{ item.nome_prazo }} · {{ textoDias(item.dias_restantes) }}
          </span>
        </li>
      </ul>
    </template>

    <!-- ===== Modo individual ===== -->
    <template v-else>
      <p v-if="carregando" class="text-sm italic text-gray-500">Montando o e-mail...</p>

      <p
        v-else-if="erroCarregar"
        class="px-4 py-3 rounded-lg border border-rose-200 bg-rose-50 text-rose-700 text-sm"
      >
        {{ erroCarregar }}
      </p>

      <p
        v-else-if="motivoIgnorado"
        class="px-4 py-3 rounded-lg border border-amber-300 bg-amber-50 text-amber-900 text-sm"
      >
        <strong>Este alerta não pode ser enviado:</strong> {{ motivoIgnorado }}
      </p>

      <div v-else-if="minuta" class="flex flex-col gap-5 text-sm">
        <!-- Para -->
        <div class="flex flex-col gap-1">
          <label for="minuta-destinatario" class="font-medium text-gray-700">Para</label>
          <input
            id="minuta-destinatario"
            v-model="destinatario"
            type="email"
            :disabled="semEmail || enviando"
            class="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100 disabled:bg-gray-100 disabled:text-gray-500"
          />
          <p v-if="semEmail" class="text-xs font-medium text-rose-600">
            Discente sem e-mail cadastrado. O envio está bloqueado.
          </p>
        </div>

        <!-- Cc (Orientadores) -->
        <div class="flex flex-col gap-2">
          <p class="font-medium text-gray-700">Cc (Orientadores)</p>
          <div class="flex flex-wrap gap-2">
            <span
              v-for="orientador in ccOrientadores"
              :key="orientador.id_professor"
              class="inline-flex items-center gap-2 pl-3 pr-1 py-1 rounded-full border text-xs"
              :class="
                ccRemovido(orientador)
                  ? 'border-gray-200 bg-gray-50 text-gray-400 line-through'
                  : 'border-blue-200 bg-blue-50 text-blue-900'
              "
            >
              <span>
                <strong>{{ orientador.nome_professor }}</strong>
                · {{ papel(orientador) }} · {{ orientador.email }}
              </span>
              <button
                type="button"
                class="px-2 py-0.5 rounded-full no-underline hover:bg-white"
                :aria-label="
                  ccRemovido(orientador)
                    ? `Colocar ${orientador.nome_professor} de volta na cópia`
                    : `Tirar ${orientador.nome_professor} da cópia`
                "
                @click="alternarCc(orientador)"
              >
                {{ ccRemovido(orientador) ? 'Voltar' : '✕' }}
              </button>
            </span>

            <span
              v-for="email in ccExtras"
              :key="email"
              class="inline-flex items-center gap-2 pl-3 pr-1 py-1 rounded-full border border-gray-300 bg-white text-xs text-gray-700"
            >
              <span>{{ email }} · Extra</span>
              <button
                type="button"
                class="px-2 py-0.5 rounded-full hover:bg-gray-100"
                :aria-label="`Tirar ${email} da cópia`"
                @click="removerCcExtra(email)"
              >
                ✕
              </button>
            </span>

            <span
              v-if="ccOrientadores.length === 0 && ccExtras.length === 0"
              class="text-xs italic text-gray-500"
            >
              Nenhum orientador com e-mail para colocar em cópia.
            </span>
          </div>

          <div class="flex flex-wrap gap-2">
            <input
              v-model="novoCc"
              type="email"
              placeholder="Adicionar outro e-mail em cópia"
              aria-label="Adicionar outro e-mail em cópia"
              class="grow min-w-[220px] px-3 py-1.5 border border-gray-300 rounded-md focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
              @keydown.enter.prevent="adicionarCc"
            />
            <button
              type="button"
              class="px-3 py-1.5 text-xs font-medium text-blue-700 border border-blue-200 rounded-md hover:bg-blue-50"
              @click="adicionarCc"
            >
              Adicionar
            </button>
          </div>
          <p v-if="erroCc" class="text-xs text-rose-600">{{ erroCc }}</p>
        </div>

        <!-- Avisos do back (ex.: orientador sem e-mail, variável desconhecida) -->
        <div
          v-if="avisosVisiveis.length"
          class="px-4 py-3 rounded-lg border border-amber-300 bg-amber-50 text-amber-900"
        >
          <p v-for="aviso in avisosVisiveis" :key="aviso">⚠ {{ aviso }}</p>
        </div>

        <!-- Assunto -->
        <div class="flex flex-col gap-1">
          <label for="minuta-assunto" class="font-medium text-gray-700">Assunto</label>
          <input
            id="minuta-assunto"
            v-model="assunto"
            type="text"
            maxlength="255"
            class="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
          />
        </div>

        <!-- Texto (miolo com variáveis) -->
        <div class="flex flex-col gap-2">
          <label for="minuta-texto" class="font-medium text-gray-700">Texto do e-mail</label>
          <p class="text-xs text-gray-500">
            A saudação ("Prezado(a) ...") e a assinatura da Secretaria entram sozinhas. As variáveis
            entre chaves são trocadas pelos dados do discente.
          </p>
          <div class="flex flex-wrap gap-2">
            <button
              v-for="variavel in variaveis"
              :key="variavel.codigo"
              type="button"
              class="px-2.5 py-1 text-xs font-medium text-gray-700 bg-gray-100 border border-gray-200 rounded-full hover:bg-gray-200"
              @click="inserirVariavel(variavel.codigo)"
            >
              + {{ variavel.rotulo }}
            </button>
          </div>
          <textarea
            id="minuta-texto"
            ref="campoTexto"
            v-model="template"
            rows="6"
            class="px-3 py-2 border border-gray-300 rounded-md font-mono text-xs leading-relaxed focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
            @input="agendarPrevia"
          ></textarea>
          <p class="text-xs text-gray-500">
            As mudanças valem só para este envio. O modelo salvo do alerta não muda.
          </p>
        </div>

        <!-- Prévia do e-mail final -->
        <div class="flex flex-col gap-2">
          <p class="font-medium text-gray-700">
            Prévia do e-mail
            <span
              v-if="!textoVazio && (atualizandoPrevia || previaDesatualizada)"
              class="font-normal text-gray-400"
            >
              (atualizando...)
            </span>
          </p>
          <p
            v-if="textoVazio"
            class="px-4 py-3 rounded-lg border border-dashed border-gray-300 text-gray-500 italic"
          >
            Escreva o texto do e-mail para ver a prévia.
          </p>
          <div
            v-else
            class="max-h-64 overflow-y-auto whitespace-pre-line px-4 py-3 rounded-lg border border-gray-200 bg-gray-50 text-gray-800"
            v-text="minuta.corpo"
          ></div>
        </div>

        <p
          v-if="erroEnvio"
          class="px-4 py-3 rounded-lg border border-rose-200 bg-rose-50 text-rose-700"
        >
          {{ erroEnvio }}
        </p>
      </div>
    </template>

    <template #rodape>
      <!-- Motivo do bloqueio ao lado dos botões, para aparecer sem precisar rolar -->
      <p
        v-if="modoIndividual && minuta && motivoBloqueio && !enviando"
        class="mr-auto self-center text-xs text-gray-500"
      >
        {{ motivoBloqueio }}
      </p>
      <BaseButton type="button" variant="secondary" :disabled="enviando" @click="fechar">
        {{ modoIndividual ? 'Cancelar' : 'Fechar' }}
      </BaseButton>
      <BaseButton
        v-if="modoIndividual"
        type="button"
        variant="primary"
        class="disabled:opacity-50 disabled:cursor-not-allowed"
        :disabled="!podeEnviar"
        @click="enviar"
      >
        {{ enviando ? 'Enviando...' : 'Confirmar e Enviar E-mail' }}
      </BaseButton>
    </template>
  </BaseModal>
</template>
