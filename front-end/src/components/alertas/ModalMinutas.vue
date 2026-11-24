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
const erroPrevia = ref('')
const itens = ref([]) // um item por aluno escolhido (veja novoItem)
const indiceAtivo = ref(0) // aluno que aparece no painel da direita
const modoEdicao = ref('todos') // lote: 'todos' (template para todos) ou 'aluno' (só este aluno)
const modelosGatilho = ref({}) // id_gatilho → texto do modelo, com variáveis
const templateBase = ref('') // "template para todos", depois que a secretaria edita
const baseEditada = ref(false)
const novoCc = ref('')
const erroCc = ref('')
const enviando = ref(false)
const erroEnvio = ref('')
const campoTexto = ref(null)

let temporizadorPrevia = null
let contadorVersao = 0
let idCarregamento = 0
const pendentesPrevia = new Set() // chaves dos itens que esperam prévia nova

const modoIndividual = computed(() => props.alertas.length === 1)
const emLote = computed(() => props.alertas.length > 1)
const itemAtivo = computed(() => itens.value[indiceAtivo.value] || null)
const editandoSoEsteAluno = computed(() => emLote.value && modoEdicao.value === 'aluno')

const titulo = computed(() =>
  modoIndividual.value
    ? `Revisar e enviar: ${props.alertas[0]?.nome_discente ?? ''}`
    : `Revisar e enviar em lote (${props.alertas.length} discentes)`,
)

// Alunos de gatilhos diferentes podem começar com textos diferentes.
const modelosDiferentes = computed(() => new Set(Object.values(modelosGatilho.value)).size > 1)

// ---------- Itens ----------

function novoItem(alerta) {
  return {
    chave: `${alerta.id_estudante}-${alerta.id_gatilho}`,
    alerta,
    minuta: null, // prévia do back: destinatário, cc, assunto, corpo, avisos
    motivoIgnorado: '', // preenchido se o alerta não está mais pendente
    destinatario: '', // só é editável no modo individual
    assunto: '',
    templateProprio: null, // texto "só para este aluno" (null = usa o template para todos)
    ccRemovidos: [], // id_professor que NÃO vão em cópia
    ccExtras: [], // e-mails a mais em cópia
    previaDesatualizada: false,
    atualizando: false,
    versao: 0,
  }
}

function mesmoAlerta(registro, item) {
  return (
    registro.id_estudante === item.alerta.id_estudante &&
    registro.id_gatilho === item.alerta.id_gatilho
  )
}

function modeloDoGatilho(item) {
  return modelosGatilho.value[item.alerta.id_gatilho] ?? TEMPLATE_PADRAO
}

// O texto (com variáveis) que vale para este aluno agora.
function templateDoItem(item) {
  if (item.templateProprio !== null) return item.templateProprio
  return baseEditada.value ? templateBase.value : modeloDoGatilho(item)
}

function semEmail(item) {
  return Boolean(item.minuta) && !item.minuta.destinatario
}

// Fica fora do envio em lote: sem e-mail ou não está mais pendente.
function excluido(item) {
  return Boolean(item.motivoIgnorado) || semEmail(item)
}

// Por que este aluno não pode ser enviado agora ('' = pode).
function motivoBloqueio(item) {
  if (!item) return ''
  if (item.motivoIgnorado) return 'Este alerta não está mais pendente.'
  if (!item.minuta) return ''
  if (semEmail(item)) return 'Discente sem e-mail cadastrado: o envio está bloqueado.'
  if (modoIndividual.value && !EMAIL_SIMPLES.test(item.destinatario.trim())) {
    return 'Informe um e-mail de destinatário válido.'
  }
  if (!item.assunto.trim()) return 'Preencha o assunto.'
  if (!templateDoItem(item).trim()) return 'Escreva o texto do e-mail.'
  if (item.atualizando || item.previaDesatualizada) return 'Aguarde a prévia atualizar.'
  return ''
}

// Ícone e frase de cada aluno na lista da esquerda (lote).
function situacao(item) {
  if (item.motivoIgnorado) {
    return { icone: '⏸', texto: 'Não está mais pendente', classe: 'text-gray-500' }
  }
  if (!item.minuta) return { icone: '…', texto: 'Carregando', classe: 'text-gray-400' }
  if (semEmail(item)) {
    return { icone: '🚫', texto: 'Sem e-mail: fica fora do envio', classe: 'text-rose-600' }
  }
  if (item.atualizando || item.previaDesatualizada) {
    return { icone: '…', texto: 'Atualizando a prévia', classe: 'text-gray-400' }
  }
  const motivo = motivoBloqueio(item)
  if (motivo) return { icone: '⚠', texto: motivo, classe: 'text-amber-700' }
  if (item.templateProprio !== null) {
    return { icone: '✏️', texto: 'Texto só para este aluno', classe: 'text-blue-700' }
  }
  return { icone: '✅', texto: 'Pronto para enviar', classe: 'text-emerald-700' }
}

const resumoLote = computed(() => ({
  prontos: itens.value.filter((i) => i.minuta && !excluido(i) && !motivoBloqueio(i)).length,
  semEmail: itens.value.filter(semEmail).length,
  naoPendentes: itens.value.filter((i) => i.motivoIgnorado).length,
}))

// O "sem e-mail" do discente já aparece em vermelho no campo Para; os outros avisos ficam no quadro amarelo.
function avisosDoItem(item) {
  return (item.minuta?.avisos || []).filter((aviso) => !aviso.startsWith('Discente sem e-mail'))
}

function papel(orientador) {
  return String(orientador.tipo_orientacao).toUpperCase().startsWith('CO')
    ? 'Coorientador'
    : 'Principal'
}

function textoDias(dias) {
  if (dias === 0) return 'vence hoje'
  if (dias === 1) return 'falta 1 dia'
  if (dias < 0) return `vencido há ${Math.abs(dias)} dia${dias === -1 ? '' : 's'}`
  return `faltam ${dias} dias`
}

// ---------- Texto que aparece na caixa (lê e escreve no lugar certo) ----------

const textoEditado = computed({
  get() {
    const item = itemAtivo.value
    if (!item) return ''
    if (editandoSoEsteAluno.value) return templateDoItem(item)
    return baseEditada.value ? templateBase.value : modeloDoGatilho(item)
  },
  set(valor) {
    const item = itemAtivo.value
    if (!item) return
    if (editandoSoEsteAluno.value) {
      item.templateProprio = valor
      marcarParaPrevia([item])
    } else {
      templateBase.value = valor
      baseEditada.value = true
      // Muda o e-mail de todos que não têm texto próprio.
      marcarParaPrevia(itens.value.filter((i) => i.templateProprio === null && !i.motivoIgnorado))
    }
  },
})

const textoAtivoVazio = computed(() => !itemAtivo.value || !templateDoItem(itemAtivo.value).trim())

// ---------- Prévias ----------

// Espera 0,6 s sem digitar antes de pedir as prévias novas ao back.
function marcarParaPrevia(lista) {
  lista.forEach((item) => {
    item.previaDesatualizada = true
    pendentesPrevia.add(item.chave)
  })
  clearTimeout(temporizadorPrevia)
  temporizadorPrevia = setTimeout(atualizarPrevias, 600)
}

// Junta os alunos que usam o mesmo texto e faz uma chamada só para cada texto.
// Texto vazio não vai para o back: ele trocaria o vazio por um texto padrão.
async function atualizarPrevias() {
  const alvo = itens.value.filter((item) => pendentesPrevia.has(item.chave))
  pendentesPrevia.clear()

  const grupos = new Map()
  alvo.forEach((item) => {
    const texto = templateDoItem(item)
    if (!texto.trim()) {
      item.versao = ++contadorVersao // descarta prévias antigas que ainda estejam a caminho
      item.atualizando = false
      return
    }
    if (!grupos.has(texto)) grupos.set(texto, [])
    grupos.get(texto).push(item)
  })

  await Promise.all([...grupos].map(([texto, grupo]) => previaDoGrupo(texto, grupo)))
}

async function previaDoGrupo(texto, grupo) {
  const versao = ++contadorVersao
  grupo.forEach((item) => {
    item.versao = versao
    item.atualizando = true
  })
  erroPrevia.value = ''
  try {
    const previa = await gerarPreviewMinutas(
      grupo.map((item) => item.alerta),
      texto,
    )
    grupo.forEach((item) => {
      if (item.versao !== versao) return // já existe uma prévia mais nova a caminho
      const nova = previa.minutas.find((m) => mesmoAlerta(m, item))
      if (nova) {
        item.minuta = nova
        item.previaDesatualizada = false
      } else {
        item.motivoIgnorado =
          previa.ignorados.find((m) => mesmoAlerta(m, item))?.motivo ||
          'Este alerta não está mais pendente.'
      }
    })
  } catch (e) {
    erroPrevia.value = e?.message || 'Não foi possível atualizar a prévia.'
  } finally {
    grupo.forEach((item) => {
      if (item.versao === versao) item.atualizando = false
    })
  }
}

// ---------- Carregar ----------

function limpar() {
  clearTimeout(temporizadorPrevia)
  pendentesPrevia.clear()
  erroCarregar.value = ''
  erroPrevia.value = ''
  itens.value = []
  indiceAtivo.value = 0
  modoEdicao.value = 'todos'
  modelosGatilho.value = {}
  templateBase.value = ''
  baseEditada.value = false
  novoCc.value = ''
  erroCc.value = ''
  erroEnvio.value = ''
}

async function carregar() {
  limpar()
  if (props.alertas.length === 0) return

  const id = ++idCarregamento
  carregando.value = true
  itens.value = props.alertas.map(novoItem)
  try {
    // As prévias e os modelos de texto (com as variáveis) vêm de rotas diferentes.
    const idsGatilho = [...new Set(props.alertas.map((a) => a.id_gatilho))]
    const [previa, gatilhos] = await Promise.all([
      gerarPreviewMinutas(props.alertas),
      Promise.all(idsGatilho.map((idGatilho) => buscarGatilho(idGatilho))),
    ])
    if (id !== idCarregamento) return // o modal foi fechado e aberto de novo

    const modelos = {}
    idsGatilho.forEach((idGatilho, i) => {
      modelos[idGatilho] = gatilhos[i]?.mensagem_template?.trim() || TEMPLATE_PADRAO
    })
    modelosGatilho.value = modelos

    itens.value.forEach((item) => {
      const minuta = previa.minutas.find((m) => mesmoAlerta(m, item))
      if (minuta) {
        item.minuta = minuta
        item.destinatario = minuta.destinatario || ''
        item.assunto = minuta.assunto || ''
      } else {
        item.motivoIgnorado =
          previa.ignorados.find((m) => mesmoAlerta(m, item))?.motivo ||
          'Este alerta não está mais pendente.'
      }
    })

    // Começa pelo primeiro aluno que pode ser enviado.
    const primeiroValido = itens.value.findIndex((item) => !excluido(item))
    indiceAtivo.value = primeiroValido >= 0 ? primeiroValido : 0
  } catch (e) {
    if (id === idCarregamento) {
      erroCarregar.value = e?.message || 'Não foi possível montar os e-mails.'
    }
  } finally {
    if (id === idCarregamento) carregando.value = false
  }
}

// ---------- Ações do painel ----------

function selecionar(indice) {
  indiceAtivo.value = indice
  novoCc.value = ''
  erroCc.value = ''
}

function desfazerTextoProprio(item) {
  item.templateProprio = null
  marcarParaPrevia([item])
}

// Coloca a variável onde está o cursor (ou no lugar do trecho selecionado).
async function inserirVariavel(codigo) {
  const campo = campoTexto.value
  const texto = textoEditado.value
  const inicio = campo ? campo.selectionStart : texto.length
  const fim = campo ? campo.selectionEnd : texto.length

  textoEditado.value = texto.slice(0, inicio) + codigo + texto.slice(fim)

  // Espera o Vue atualizar a caixa de texto e devolve o cursor para depois da variável.
  await nextTick()
  if (campo) {
    const posicao = inicio + codigo.length
    campo.focus()
    campo.setSelectionRange(posicao, posicao)
  }
}

function ccRemovido(item, orientador) {
  return item.ccRemovidos.includes(orientador.id_professor)
}

function alternarCc(item, orientador) {
  const id = orientador.id_professor
  item.ccRemovidos = ccRemovido(item, orientador)
    ? item.ccRemovidos.filter((valor) => valor !== id)
    : [...item.ccRemovidos, id]
}

function adicionarCc(item) {
  erroCc.value = ''
  const email = novoCc.value.trim()
  if (!email) return
  if (!EMAIL_SIMPLES.test(email)) {
    erroCc.value = 'E-mail inválido.'
    return
  }
  const destino = modoIndividual.value ? item.destinatario : item.minuta?.destinatario
  const jaExiste = [
    destino,
    ...(item.minuta?.destinatarios_cc || []).map((o) => o.email),
    ...item.ccExtras,
  ].some(
    (valor) =>
      String(valor ?? '')
        .trim()
        .toLowerCase() === email.toLowerCase(),
  )
  if (jaExiste) {
    erroCc.value = 'Esse e-mail já está no envio.'
    return
  }
  item.ccExtras = [...item.ccExtras, email]
  novoCc.value = ''
}

function removerCcExtra(item, email) {
  item.ccExtras = item.ccExtras.filter((valor) => valor !== email)
}

// ---------- Envio individual ----------

const podeEnviarIndividual = computed(() => {
  const item = itemAtivo.value
  return modoIndividual.value && Boolean(item?.minuta) && !motivoBloqueio(item) && !enviando.value
})

async function enviarIndividual() {
  if (!podeEnviarIndividual.value) return
  const item = itemAtivo.value
  enviando.value = true
  erroEnvio.value = ''

  // O corpo vai pronto (a prévia do back): o back não preenche variáveis no envio.
  const dados = {
    id_estudante: item.alerta.id_estudante,
    id_gatilho: item.alerta.id_gatilho,
    assunto: item.assunto.trim(),
    corpo_mensagem: item.minuta.corpo,
  }
  const destino = item.destinatario.trim()
  if (destino.toLowerCase() !== String(item.minuta.destinatario).toLowerCase()) {
    dados.email_destino = destino
  }
  if (item.ccRemovidos.length) dados.ignorar_cc_ids = [...item.ccRemovidos]
  if (item.ccExtras.length) dados.cc_adicionais = [...item.ccExtras]

  try {
    const registro = await dispararIndividual(dados)
    emit('enviado', { registro, nome: item.alerta.nome_discente })
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

// Sempre que o modal abre, monta os e-mails do zero.
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
    :larguraMaxima="emLote ? '1040px' : '760px'"
    @fechar="fechar"
  >
    <p v-if="carregando" class="text-sm italic text-gray-500">Montando os e-mails...</p>

    <p
      v-else-if="erroCarregar"
      class="px-4 py-3 rounded-lg border border-rose-200 bg-rose-50 text-rose-700 text-sm"
    >
      {{ erroCarregar }}
    </p>

    <p
      v-else-if="modoIndividual && itemAtivo?.motivoIgnorado"
      class="px-4 py-3 rounded-lg border border-amber-300 bg-amber-50 text-amber-900 text-sm"
    >
      <strong>Este alerta não pode ser enviado:</strong> {{ itemAtivo.motivoIgnorado }}
    </p>

    <div v-else-if="itemAtivo" :class="emLote ? 'grid gap-6 md:grid-cols-[260px_1fr]' : ''">
      <!-- ===== Lote: lista dos discentes ===== -->
      <aside v-if="emLote" class="flex flex-col gap-2">
        <p class="text-xs font-semibold uppercase tracking-wider text-gray-500">
          Discentes ({{ itens.length }})
        </p>
        <ul
          class="max-h-[60vh] overflow-y-auto divide-y divide-gray-100 border border-gray-200 rounded-lg"
        >
          <li v-for="(item, indice) in itens" :key="item.chave">
            <button
              type="button"
              class="w-full flex items-start gap-2 px-3 py-2.5 text-left transition-colors"
              :class="indice === indiceAtivo ? 'bg-blue-50' : 'hover:bg-gray-50'"
              :aria-current="indice === indiceAtivo ? 'true' : undefined"
              @click="selecionar(indice)"
            >
              <span aria-hidden="true">{{ situacao(item).icone }}</span>
              <span class="min-w-0">
                <span
                  class="block text-sm font-medium leading-snug"
                  :class="excluido(item) ? 'text-gray-400 line-through' : 'text-gray-900'"
                >
                  {{ item.alerta.nome_discente }}
                </span>
                <span class="block text-xs text-gray-500">
                  {{ item.alerta.nome_prazo }} · {{ textoDias(item.alerta.dias_restantes) }}
                </span>
                <span class="block text-xs" :class="situacao(item).classe">
                  {{ situacao(item).texto }}
                </span>
              </span>
            </button>
          </li>
        </ul>
      </aside>

      <!-- ===== Painel do e-mail (do aluno escolhido) ===== -->
      <section class="flex flex-col gap-5 min-w-0 text-sm">
        <p v-if="emLote" class="text-base font-semibold text-gray-900">
          {{ itemAtivo.alerta.nome_discente }}
          <span class="font-normal text-gray-500">· {{ itemAtivo.alerta.nome_prazo }}</span>
        </p>

        <p
          v-if="emLote && itemAtivo.motivoIgnorado"
          class="px-4 py-3 rounded-lg border border-amber-300 bg-amber-50 text-amber-900"
        >
          <strong>Fica fora do envio:</strong> {{ itemAtivo.motivoIgnorado }}
        </p>

        <template v-else-if="itemAtivo.minuta">
          <!-- Para -->
          <div class="flex flex-col gap-1">
            <label for="minuta-destinatario" class="font-medium text-gray-700">Para</label>
            <input
              v-if="modoIndividual"
              id="minuta-destinatario"
              v-model="itemAtivo.destinatario"
              type="email"
              :disabled="semEmail(itemAtivo) || enviando"
              class="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100 disabled:bg-gray-100 disabled:text-gray-500"
            />
            <p
              v-else
              id="minuta-destinatario"
              class="px-3 py-2 rounded-md border border-gray-200 bg-gray-50 text-gray-700"
            >
              {{ itemAtivo.minuta.destinatario || '—' }}
            </p>
            <p v-if="semEmail(itemAtivo)" class="text-xs font-medium text-rose-600">
              Discente sem e-mail cadastrado. O envio está bloqueado{{
                emLote ? ' e ele fica fora do lote' : ''
              }}.
            </p>
          </div>

          <!-- Cc (Orientadores) -->
          <div class="flex flex-col gap-2">
            <p class="font-medium text-gray-700">Cc (Orientadores)</p>
            <div class="flex flex-wrap gap-2">
              <span
                v-for="orientador in itemAtivo.minuta.destinatarios_cc || []"
                :key="orientador.id_professor"
                class="inline-flex items-center gap-2 pl-3 pr-1 py-1 rounded-full border text-xs"
                :class="
                  ccRemovido(itemAtivo, orientador)
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
                    ccRemovido(itemAtivo, orientador)
                      ? `Colocar ${orientador.nome_professor} de volta na cópia`
                      : `Tirar ${orientador.nome_professor} da cópia`
                  "
                  @click="alternarCc(itemAtivo, orientador)"
                >
                  {{ ccRemovido(itemAtivo, orientador) ? 'Voltar' : '✕' }}
                </button>
              </span>

              <span
                v-for="email in itemAtivo.ccExtras"
                :key="email"
                class="inline-flex items-center gap-2 pl-3 pr-1 py-1 rounded-full border border-gray-300 bg-white text-xs text-gray-700"
              >
                <span>{{ email }} · Extra</span>
                <button
                  type="button"
                  class="px-2 py-0.5 rounded-full hover:bg-gray-100"
                  :aria-label="`Tirar ${email} da cópia`"
                  @click="removerCcExtra(itemAtivo, email)"
                >
                  ✕
                </button>
              </span>

              <span
                v-if="
                  !(itemAtivo.minuta.destinatarios_cc || []).length && !itemAtivo.ccExtras.length
                "
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
                @keydown.enter.prevent="adicionarCc(itemAtivo)"
              />
              <button
                type="button"
                class="px-3 py-1.5 text-xs font-medium text-blue-700 border border-blue-200 rounded-md hover:bg-blue-50"
                @click="adicionarCc(itemAtivo)"
              >
                Adicionar
              </button>
            </div>
            <p v-if="erroCc" class="text-xs text-rose-600">{{ erroCc }}</p>
          </div>

          <!-- Avisos do back (ex.: orientador sem e-mail, variável desconhecida) -->
          <div
            v-if="avisosDoItem(itemAtivo).length"
            class="px-4 py-3 rounded-lg border border-amber-300 bg-amber-50 text-amber-900"
          >
            <p v-for="aviso in avisosDoItem(itemAtivo)" :key="aviso">⚠ {{ aviso }}</p>
          </div>

          <!-- Assunto -->
          <div class="flex flex-col gap-1">
            <label for="minuta-assunto" class="font-medium text-gray-700">Assunto</label>
            <input
              id="minuta-assunto"
              v-model="itemAtivo.assunto"
              type="text"
              maxlength="255"
              class="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
            />
          </div>

          <!-- Texto (miolo com variáveis) -->
          <div class="flex flex-col gap-2">
            <label for="minuta-texto" class="font-medium text-gray-700">Texto do e-mail</label>

            <!-- Lote: escolher se a edição vale para todos ou só para este aluno -->
            <div
              v-if="emLote"
              class="inline-flex self-start p-0.5 rounded-lg border border-gray-200 bg-gray-50"
              role="group"
              aria-label="Como editar o texto"
            >
              <button
                type="button"
                class="px-3 py-1.5 text-xs font-medium rounded-md"
                :class="
                  modoEdicao === 'todos'
                    ? 'bg-white text-gray-900 shadow-sm'
                    : 'text-gray-500 hover:text-gray-800'
                "
                :aria-pressed="modoEdicao === 'todos'"
                @click="modoEdicao = 'todos'"
              >
                Template para todos
              </button>
              <button
                type="button"
                class="px-3 py-1.5 text-xs font-medium rounded-md"
                :class="
                  modoEdicao === 'aluno'
                    ? 'bg-white text-gray-900 shadow-sm'
                    : 'text-gray-500 hover:text-gray-800'
                "
                :aria-pressed="modoEdicao === 'aluno'"
                @click="modoEdicao = 'aluno'"
              >
                Só para este aluno
              </button>
            </div>

            <p class="text-xs text-gray-500">
              A saudação ("Prezado(a) ...") e a assinatura da Secretaria entram sozinhas. As
              variáveis entre chaves são trocadas pelos dados de cada discente.
            </p>

            <template v-if="emLote">
              <p v-if="modoEdicao === 'todos'" class="text-xs text-gray-500">
                O que você escrever aqui vale para todos os discentes que não têm texto próprio.
              </p>
              <p v-else class="text-xs text-gray-500">
                O que você escrever aqui vale só para {{ itemAtivo.alerta.nome_discente }}.
                <button
                  v-if="itemAtivo.templateProprio !== null"
                  type="button"
                  class="font-medium text-blue-700 hover:underline"
                  @click="desfazerTextoProprio(itemAtivo)"
                >
                  Desfazer e usar o template para todos
                </button>
              </p>

              <p
                v-if="modoEdicao === 'todos' && itemAtivo.templateProprio !== null"
                class="px-3 py-2 rounded-lg border border-amber-300 bg-amber-50 text-xs text-amber-900"
              >
                Este aluno tem um texto só para ele, então o template para todos não muda o e-mail
                dele.
                <button
                  type="button"
                  class="font-medium underline"
                  @click="desfazerTextoProprio(itemAtivo)"
                >
                  Voltar a usar o template para todos
                </button>
              </p>

              <p
                v-if="modoEdicao === 'todos' && modelosDiferentes && !baseEditada"
                class="px-3 py-2 rounded-lg border border-amber-300 bg-amber-50 text-xs text-amber-900"
              >
                Os discentes escolhidos têm modelos de texto diferentes, e cada um começa com o seu.
                Se você editar o template para todos, este texto passa a valer para todos (as
                variáveis, como {nome_prazo}, se ajustam a cada um).
              </p>
            </template>

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
              v-model="textoEditado"
              rows="6"
              class="px-3 py-2 border border-gray-300 rounded-md font-mono text-xs leading-relaxed focus:outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
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
                v-if="!textoAtivoVazio && (itemAtivo.atualizando || itemAtivo.previaDesatualizada)"
                class="font-normal text-gray-400"
              >
                (atualizando...)
              </span>
            </p>
            <p
              v-if="textoAtivoVazio"
              class="px-4 py-3 rounded-lg border border-dashed border-gray-300 text-gray-500 italic"
            >
              Escreva o texto do e-mail para ver a prévia.
            </p>
            <div
              v-else
              class="max-h-64 overflow-y-auto whitespace-pre-line px-4 py-3 rounded-lg border border-gray-200 bg-gray-50 text-gray-800"
              v-text="itemAtivo.minuta.corpo"
            ></div>
          </div>

          <p
            v-if="erroPrevia"
            class="px-4 py-3 rounded-lg border border-rose-200 bg-rose-50 text-rose-700"
          >
            {{ erroPrevia }}
          </p>
          <p
            v-if="erroEnvio"
            class="px-4 py-3 rounded-lg border border-rose-200 bg-rose-50 text-rose-700"
          >
            {{ erroEnvio }}
          </p>
        </template>
      </section>
    </div>

    <template #rodape>
      <!-- Individual: motivo do bloqueio ao lado dos botões, para aparecer sem precisar rolar -->
      <p
        v-if="modoIndividual && itemAtivo?.minuta && motivoBloqueio(itemAtivo) && !enviando"
        class="mr-auto self-center text-xs text-gray-500"
      >
        {{ motivoBloqueio(itemAtivo) }}
      </p>
      <!-- Lote: resumo de quem vai e quem fica fora -->
      <p
        v-if="emLote && itens.length && !carregando"
        class="mr-auto self-center text-xs text-gray-500"
      >
        {{ resumoLote.prontos }} pronto(s) para enviar · {{ resumoLote.semEmail }} sem e-mail ·
        {{ resumoLote.naoPendentes }} não pendente(s)
      </p>

      <BaseButton type="button" variant="secondary" :disabled="enviando" @click="fechar">
        {{ modoIndividual ? 'Cancelar' : 'Fechar' }}
      </BaseButton>
      <BaseButton
        v-if="modoIndividual"
        type="button"
        variant="primary"
        class="disabled:opacity-50 disabled:cursor-not-allowed"
        :disabled="!podeEnviarIndividual"
        @click="enviarIndividual"
      >
        {{ enviando ? 'Enviando...' : 'Confirmar e Enviar E-mail' }}
      </BaseButton>
    </template>
  </BaseModal>
</template>
