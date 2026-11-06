<script setup>
import { ref, computed, watch, onBeforeUnmount } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import DefaultLayout from '../layouts/DefaultLayout.vue'
import BaseButton from '../components/BaseButton.vue'
import BaseModal from '../components/BaseModal.vue'
import { useAuthStore } from '../stores/auth'
import CardEstagios from '../components/estudante/CardEstagios.vue'
import CardProficiencia from '../components/estudante/CardProficiencia.vue'
import CardArtigos from '../components/estudante/CardArtigos.vue'
import CardTrabalhoFinal from '../components/estudante/CardTrabalhoFinal.vue'

const api = 'http://localhost:8000'
const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const estudante = ref(null)
const nomeOrientador = ref('')
const codigoSemestre = ref('')
const carregando = ref(true)
const erro = ref('')

const professores = ref([])

const aviso = ref(null)
let temporizadorAviso = null

const diasParaAvisoPrazo = 180
const statusSemAvisoPrazo = ['TITULADO', 'DESLIGADO']

const opcoesStatus = [
  'ATIVO',
  'TRANCADO',
  'PROCESSO DE DESLIGAMENTO',
  'DESLIGADO',
  'PÓS DEFESA',
  'TITULADO',
]

const classesStatus = {
  ATIVO: 'status-ativo',
  TRANCADO: 'status-trancado',
  'PROCESSO DE DESLIGAMENTO': 'status-desligamento',
  DESLIGADO: 'status-desligado',
  'PÓS DEFESA': 'status-pos-defesa',
  TITULADO: 'status-titulado',
}

// ---------- Modal: Editar perfil ----------
const modalPerfilAberto = ref(false)
const salvandoPerfil = ref(false)
const erroPerfil = ref('')
const formPerfil = ref({})

// ---------- Prorrogações ----------
// Valores iguais aos do backend (back-end/db/enumStatus.py).
const tiposPrazoProrrogacao = [
  { valor: 'QUALIFICACAO', rotulo: 'Qualificação' },
  { valor: 'DEFESA', rotulo: 'Defesa' },
]
const resultadosProrrogacao = [
  { valor: 'EM ANÁLISE', rotulo: 'Em análise', classe: 'resultado-analise' },
  { valor: 'DEFERIDO', rotulo: 'Deferido', classe: 'resultado-deferido' },
  { valor: 'INDEFERIDO', rotulo: 'Indeferido', classe: 'resultado-indeferido' },
]

const prorrogacoes = ref([])
const carregandoProrrogacoes = ref(false)
const erroProrrogacoes = ref('')

const modalProrrogacaoAberto = ref(false)
const salvandoProrrogacao = ref(false)
const erroProrrogacao = ref('')
const editandoProrrogacaoId = ref(null)
const formProrrogacao = ref({})

const professoresOrdenados = computed(() =>
  [...professores.value].sort((a, b) => a.nome_professor.localeCompare(b.nome_professor, 'pt-BR')),
)

const prorrogacoesOrdenadas = computed(() =>
  [...prorrogacoes.value].sort((a, b) =>
    String(b.data_pedido || '').localeCompare(String(a.data_pedido || '')),
  ),
)

const iniciaisEstudante = computed(() => {
  const partes = (estudante.value?.nome_discente || '').trim().split(/\s+/).filter(Boolean)
  if (partes.length === 0) return '?'
  const primeira = partes[0][0]
  const ultima = partes.length > 1 ? partes[partes.length - 1][0] : ''
  return (primeira + ultima).toUpperCase()
})

const avisoPrazo = computed(() => {
  if (!estudante.value) return null
  if (statusSemAvisoPrazo.includes(estudante.value.status_atual)) return null
  const dias = diasAtePrazo(estudante.value.prazo_conclusao_sigaa)
  if (dias === null) return null
  if (dias < 0) return { classe: 'prazo-vencido', texto: `Prazo vencido há ${textoDias(-dias)}` }
  if (dias === 0) return { classe: 'prazo-proximo', texto: 'O prazo termina hoje' }
  if (dias <= diasParaAvisoPrazo) {
    return { classe: 'prazo-proximo', texto: `Faltam ${textoDias(dias)} para o prazo` }
  }
  return null
})

function classeDoStatus(status) {
  return classesStatus[status] || 'status-desligado'
}

function formatarData(texto) {
  if (!texto) return '—'
  const [ano, mes, dia] = texto.slice(0, 10).split('-')
  if (!ano || !mes || !dia) return texto
  return `${dia}/${mes}/${ano}`
}

function diasAtePrazo(texto) {
  if (!texto) return null
  const [ano, mes, dia] = texto.slice(0, 10).split('-').map(Number)
  if (!ano || !mes || !dia) return null
  const prazo = new Date(ano, mes - 1, dia)
  const agora = new Date()
  const hoje = new Date(agora.getFullYear(), agora.getMonth(), agora.getDate())
  return Math.round((prazo - hoje) / (1000 * 60 * 60 * 24))
}

function textoDias(quantidade) {
  return quantidade === 1 ? '1 dia' : `${quantidade} dias`
}

function textoMeses(quantidade) {
  return Number(quantidade) === 1 ? '1 mês' : `${quantidade} meses`
}

function dataDeHoje() {
  const agora = new Date()
  const mes = String(agora.getMonth() + 1).padStart(2, '0')
  const dia = String(agora.getDate()).padStart(2, '0')
  return `${agora.getFullYear()}-${mes}-${dia}`
}

function rotuloTipoPrazo(valor) {
  return tiposPrazoProrrogacao.find((t) => t.valor === valor)?.rotulo || valor || '—'
}

function rotuloResultado(valor) {
  if (!valor) return 'Sem resultado'
  return resultadosProrrogacao.find((r) => r.valor === valor)?.rotulo || valor
}

function classeResultado(valor) {
  return resultadosProrrogacao.find((r) => r.valor === valor)?.classe || 'badge-neutro'
}

function cabecalho() {
  return { Authorization: `Bearer ${authStore.token}` }
}

function mostrarAviso(texto, tipo) {
  aviso.value = { texto, tipo }
  clearTimeout(temporizadorAviso)
  temporizadorAviso = setTimeout(() => {
    aviso.value = null
  }, 3000)
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

function voltar() {
  // Se veio de outra tela do sistema (ex.: a listagem com filtros), volta para ela.
  if (window.history.state?.back) {
    router.back()
  } else {
    router.push('/estudantes')
  }
}

// ---------- Pedidos à API ----------

async function buscarOrientador(idOrientador) {
  if (!idOrientador) return
  try {
    const resposta = await fetch(`${api}/professores/${idOrientador}`, { headers: cabecalho() })
    if (!resposta.ok) return
    const professor = await resposta.json()
    nomeOrientador.value = professor.nome_professor
  } catch {
    // Sem o nome, a tela mostra "Professor" e o número.
  }
}

async function buscarSemestre(idSemestre) {
  if (!idSemestre) return
  try {
    const resposta = await fetch(`${api}/configuracoes/semestres/${idSemestre}`, {
      headers: cabecalho(),
    })
    if (!resposta.ok) return
    const semestre = await resposta.json()
    codigoSemestre.value = semestre.codigo_semestre
  } catch {
    // Sem o código, a tela mostra o número do semestre.
  }
}

async function buscarProfessores() {
  try {
    const resposta = await fetch(`${api}/professores?limit=200`, { headers: cabecalho() })
    if (!resposta.ok) return
    professores.value = await resposta.json()
  } catch {
    // Sem a lista, o campo de orientador mostra só "Sem orientador".
  }
}

async function buscarProrrogacoes(idEstudante) {
  carregandoProrrogacoes.value = true
  erroProrrogacoes.value = ''
  try {
    const resposta = await fetch(`${api}/prorrogacoes/estudante/${idEstudante}`, {
      headers: cabecalho(),
    })
    if (resposta.status === 404) {
      prorrogacoes.value = []
      return
    }
    if (!resposta.ok) {
      erroProrrogacoes.value = 'Não foi possível carregar as prorrogações.'
      return
    }
    prorrogacoes.value = await resposta.json()
  } catch {
    erroProrrogacoes.value = 'Não foi possível carregar as prorrogações.'
  } finally {
    carregandoProrrogacoes.value = false
  }
}

async function carregarEstudante() {
  estudante.value = null
  nomeOrientador.value = ''
  codigoSemestre.value = ''
  prorrogacoes.value = []
  erro.value = ''

  const id = Number(route.params.id)
  if (!Number.isInteger(id) || id < 1) {
    erro.value = 'Estudante não encontrado.'
    carregando.value = false
    return
  }

  carregando.value = true
  try {
    const resposta = await fetch(`${api}/estudantes/${id}`, { headers: cabecalho() })
    if (Number(route.params.id) !== id) return
    if (!resposta.ok) {
      if (resposta.status === 401) {
        erro.value = 'Sua sessão expirou. Saia e entre de novo.'
      } else if (resposta.status === 404) {
        erro.value = 'Estudante não encontrado.'
      } else {
        erro.value = `Não foi possível carregar o estudante (erro ${resposta.status}).`
      }
      return
    }
    const dados = await resposta.json()
    if (Number(route.params.id) !== id) return
    estudante.value = dados
    // Os cards dos marcos carregam sozinhos, sem segurar o resto da tela.
    buscarProrrogacoes(id)
    await Promise.all([buscarOrientador(dados.id_orientador), buscarSemestre(dados.id_semestre)])
  } catch {
    erro.value = 'Não foi possível conectar ao servidor. Verifique se o backend está ligado.'
  } finally {
    carregando.value = false
  }
}

// ---------- Modal: Editar perfil ----------

function abrirModalPerfil() {
  formPerfil.value = {
    nome_discente: estudante.value.nome_discente || '',
    email: estudante.value.email || '',
    id_orientador: estudante.value.id_orientador || '',
    status_atual: estudante.value.status_atual,
    prazo_conclusao_sigaa: (estudante.value.prazo_conclusao_sigaa || '').slice(0, 10),
    eh_bolsista: Boolean(estudante.value.eh_bolsista),
  }
  erroPerfil.value = ''
  if (professores.value.length === 0) buscarProfessores()
  modalPerfilAberto.value = true
}

function fecharModalPerfil() {
  if (salvandoPerfil.value) return
  modalPerfilAberto.value = false
}

async function salvarPerfil() {
  const nome = formPerfil.value.nome_discente.trim()
  if (!nome) {
    erroPerfil.value = 'Informe o nome do estudante.'
    return
  }

  const dados = {
    nome_discente: nome,
    email: formPerfil.value.email.trim() || null,
    id_orientador: formPerfil.value.id_orientador || null,
    eh_bolsista: formPerfil.value.eh_bolsista,
    prazo_conclusao_sigaa: formPerfil.value.prazo_conclusao_sigaa || null,
    status_atual: formPerfil.value.status_atual,
  }

  erroPerfil.value = ''
  salvandoPerfil.value = true
  try {
    const resposta = await fetch(`${api}/estudantes/${estudante.value.id_estudante}`, {
      method: 'PUT',
      headers: { ...cabecalho(), 'Content-Type': 'application/json' },
      body: JSON.stringify(dados),
    })

    if (!resposta.ok) {
      const detalhe = await lerMensagemDeErro(resposta)
      if (resposta.status === 401) {
        erroPerfil.value = 'Sua sessão expirou. Saia e entre de novo.'
      } else if (resposta.status === 403) {
        erroPerfil.value = 'Você não tem permissão para editar este estudante.'
      } else {
        erroPerfil.value = detalhe || 'Não foi possível salvar. Confira os dados.'
      }
      return
    }

    // Atualiza o card na hora, sem recarregar a página.
    estudante.value = { ...estudante.value, ...dados }
    const professor = professores.value.find((p) => p.id_professor === dados.id_orientador)
    nomeOrientador.value = professor ? professor.nome_professor : ''

    modalPerfilAberto.value = false
    mostrarAviso('Perfil atualizado.', 'sucesso')
  } catch {
    erroPerfil.value = 'Não foi possível conectar ao servidor.'
  } finally {
    salvandoPerfil.value = false
  }
}

// ---------- Modal: Prorrogação ----------

function abrirModalProrrogacao(prorrogacao = null) {
  editandoProrrogacaoId.value = prorrogacao ? prorrogacao.id_prorrogacao : null
  formProrrogacao.value = prorrogacao
    ? {
        tipo_prazo: prorrogacao.tipo_prazo || '',
        quantidade_meses: prorrogacao.quantidade_meses ?? '',
        data_pedido: (prorrogacao.data_pedido || '').slice(0, 10),
        resultado_pedido: prorrogacao.resultado_pedido || '',
      }
    : {
        tipo_prazo: '',
        quantidade_meses: '',
        data_pedido: dataDeHoje(),
        resultado_pedido: 'EM ANÁLISE',
      }
  erroProrrogacao.value = ''
  modalProrrogacaoAberto.value = true
}

function fecharModalProrrogacao() {
  if (salvandoProrrogacao.value) return
  modalProrrogacaoAberto.value = false
}

function validarProrrogacao() {
  if (!formProrrogacao.value.tipo_prazo) return 'Escolha o prazo que será prorrogado.'
  const meses = Number(formProrrogacao.value.quantidade_meses)
  if (formProrrogacao.value.quantidade_meses === '' || !Number.isInteger(meses) || meses < 1) {
    return 'A quantidade de meses precisa ser um número inteiro maior que 0.'
  }
  if (!formProrrogacao.value.data_pedido) return 'Informe a data do pedido.'
  return ''
}

async function salvarProrrogacao() {
  erroProrrogacao.value = validarProrrogacao()
  if (erroProrrogacao.value) return

  const editando = editandoProrrogacaoId.value !== null
  const dados = {
    id_estudante: estudante.value.id_estudante,
    tipo_prazo: formProrrogacao.value.tipo_prazo,
    quantidade_meses: Number(formProrrogacao.value.quantidade_meses),
    data_pedido: formProrrogacao.value.data_pedido,
    resultado_pedido: formProrrogacao.value.resultado_pedido || null,
  }
  const url = editando
    ? `${api}/prorrogacoes/${editandoProrrogacaoId.value}`
    : `${api}/prorrogacoes`

  salvandoProrrogacao.value = true
  try {
    const resposta = await fetch(url, {
      method: editando ? 'PUT' : 'POST',
      headers: { ...cabecalho(), 'Content-Type': 'application/json' },
      body: JSON.stringify(dados),
    })

    if (!resposta.ok) {
      const detalhe = await lerMensagemDeErro(resposta)
      if (resposta.status === 401) {
        erroProrrogacao.value = 'Sua sessão expirou. Saia e entre de novo.'
      } else if (resposta.status === 403) {
        erroProrrogacao.value = 'Você não tem permissão para registrar prorrogações.'
      } else {
        erroProrrogacao.value = detalhe || 'Não foi possível salvar. Confira os dados.'
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
    if (salva && salva.id_prorrogacao) {
      if (editando) {
        prorrogacoes.value = prorrogacoes.value.map((p) =>
          p.id_prorrogacao === salva.id_prorrogacao ? salva : p,
        )
      } else {
        prorrogacoes.value = [...prorrogacoes.value, salva]
      }
    } else {
      buscarProrrogacoes(estudante.value.id_estudante)
    }

    modalProrrogacaoAberto.value = false
    mostrarAviso(editando ? 'Prorrogação atualizada.' : 'Prorrogação registrada.', 'sucesso')
  } catch {
    erroProrrogacao.value = 'Não foi possível conectar ao servidor.'
  } finally {
    salvandoProrrogacao.value = false
  }
}

watch(() => route.params.id, carregarEstudante, { immediate: true })

onBeforeUnmount(() => {
  clearTimeout(temporizadorAviso)
})
</script>

<template>
  <DefaultLayout>
    <div
      v-if="aviso"
      class="aviso-flutuante"
      :class="aviso.tipo === 'erro' ? 'aviso-flutuante-erro' : 'aviso-flutuante-sucesso'"
      role="status"
    >
      {{ aviso.texto }}
    </div>

    <button type="button" class="link-voltar" @click="voltar">← Voltar para estudantes</button>

    <div v-if="carregando" class="estado">Carregando estudante...</div>

    <div v-else-if="erro" class="aviso-erro">{{ erro }}</div>

    <template v-else-if="estudante">
      <section class="card">
        <div class="perfil-topo">
          <div class="perfil-identidade">
            <span class="avatar">{{ iniciaisEstudante }}</span>
            <div>
              <h1>{{ estudante.nome_discente }}</h1>
              <div class="perfil-selos">
                <span class="badge" :class="classeDoStatus(estudante.status_atual)">
                  {{ estudante.status_atual }}
                </span>
                <span v-if="estudante.eh_bolsista" class="selo-bolsista">Bolsista</span>
              </div>
            </div>
          </div>
          <BaseButton type="button" variant="secondary" @click="abrirModalPerfil">
            Editar perfil
          </BaseButton>
        </div>

        <dl class="dados-grid">
          <div>
            <dt>Matrícula</dt>
            <dd>{{ estudante.matricula }}</dd>
          </div>
          <div>
            <dt>E-mail</dt>
            <dd v-if="estudante.email">{{ estudante.email }}</dd>
            <dd v-else class="texto-vazio">Sem e-mail</dd>
          </div>
          <div>
            <dt>Orientador</dt>
            <dd v-if="estudante.id_orientador">
              {{ nomeOrientador || `Professor ${estudante.id_orientador}` }}
            </dd>
            <dd v-else class="texto-vazio">Sem orientador</dd>
          </div>
          <div>
            <dt>Semestre de ingresso</dt>
            <dd>{{ codigoSemestre || estudante.id_semestre }}</dd>
          </div>
          <div>
            <dt>Prazo (SIGAA)</dt>
            <dd class="dado-prazo">
              <span>{{ formatarData(estudante.prazo_conclusao_sigaa) }}</span>
              <span
                v-if="avisoPrazo"
                class="alerta-prazo"
                :class="avisoPrazo.classe"
                role="img"
                :title="avisoPrazo.texto"
                :aria-label="avisoPrazo.texto"
              >
                !
              </span>
              <span v-if="avisoPrazo" class="texto-prazo">{{ avisoPrazo.texto }}</span>
            </dd>
          </div>
        </dl>
      </section>
     
      <CardProficiencia :id-estudante="estudante.id_estudante" @aviso="mostrarAviso" />
      <CardArtigos :id-estudante="estudante.id_estudante" @aviso="mostrarAviso" />
      <CardEstagios
        :id-estudante="estudante.id_estudante"
        :id-orientador="estudante.id_orientador"
        @aviso="mostrarAviso"
      />
      <CardTrabalhoFinal :id-estudante="estudante.id_estudante" @aviso="mostrarAviso" />
      <section class="card">
        <div class="card-topo">
          <h2>Prorrogações</h2>
          <BaseButton type="button" variant="secondary" @click="abrirModalProrrogacao()">
            Adicionar prorrogação
          </BaseButton>
        </div>

        <p v-if="carregandoProrrogacoes" class="texto-vazio">Carregando prorrogações...</p>
        <p v-else-if="erroProrrogacoes" class="aviso-erro">{{ erroProrrogacoes }}</p>
        <p v-else-if="prorrogacoes.length === 0" class="texto-vazio">
          Nenhum pedido de prorrogação.
        </p>
        <div v-else class="tabela-rolagem">
          <table class="tabela-simples">
            <thead>
              <tr>
                <th>Data do pedido</th>
                <th>Prazo</th>
                <th>Meses</th>
                <th>Resultado</th>
                <th class="coluna-acoes"><span class="visualmente-oculto">Ações</span></th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="prorrogacao in prorrogacoesOrdenadas" :key="prorrogacao.id_prorrogacao">
                <td>{{ formatarData(prorrogacao.data_pedido) }}</td>
                <td>{{ rotuloTipoPrazo(prorrogacao.tipo_prazo) }}</td>
                <td>{{ textoMeses(prorrogacao.quantidade_meses) }}</td>
                <td>
                  <span class="badge" :class="classeResultado(prorrogacao.resultado_pedido)">
                    {{ rotuloResultado(prorrogacao.resultado_pedido) }}
                  </span>
                </td>
                <td class="coluna-acoes">
                  <button
                    type="button"
                    class="botao-tabela"
                    :aria-label="`Editar prorrogação de ${formatarData(prorrogacao.data_pedido)}`"
                    @click="abrirModalProrrogacao(prorrogacao)"
                  >
                    Editar
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      <BaseModal :aberto="modalPerfilAberto" titulo="Editar perfil" @fechar="fecharModalPerfil">
        <form id="form-editar-perfil" class="form-grid" @submit.prevent="salvarPerfil">
          <div class="form-group span-full">
            <label for="perfil-nome">Nome completo *</label>
            <input id="perfil-nome" v-model="formPerfil.nome_discente" type="text" required />
          </div>

          <div class="form-group span-full">
            <label for="perfil-email">E-mail</label>
            <input id="perfil-email" v-model="formPerfil.email" type="email" />
          </div>

          <div class="form-group">
            <label for="perfil-orientador">Orientador</label>
            <select id="perfil-orientador" v-model="formPerfil.id_orientador">
              <option value="">Sem orientador</option>
              <option
                v-for="professor in professoresOrdenados"
                :key="professor.id_professor"
                :value="professor.id_professor"
              >
                {{ professor.nome_professor }}
              </option>
            </select>
          </div>

          <div class="form-group">
            <label for="perfil-status">Status *</label>
            <select id="perfil-status" v-model="formPerfil.status_atual" required>
              <option v-for="status in opcoesStatus" :key="status" :value="status">
                {{ status }}
              </option>
            </select>
          </div>

          <div class="form-group">
            <label for="perfil-prazo">Prazo de conclusão (SIGAA)</label>
            <input id="perfil-prazo" v-model="formPerfil.prazo_conclusao_sigaa" type="date" />
          </div>

          <div class="form-group-checkbox">
            <input id="perfil-bolsista" v-model="formPerfil.eh_bolsista" type="checkbox" />
            <label for="perfil-bolsista">Estudante bolsista</label>
          </div>

          <p class="dica span-full">
            Matrícula ({{ estudante.matricula }}) e semestre de ingresso não podem ser alterados.
          </p>

          <p v-if="erroPerfil" class="aviso-erro span-full">{{ erroPerfil }}</p>
        </form>

        <template #rodape>
          <BaseButton
            type="button"
            variant="secondary"
            :disabled="salvandoPerfil"
            @click="fecharModalPerfil"
          >
            Cancelar
          </BaseButton>
          <BaseButton
            type="submit"
            form="form-editar-perfil"
            variant="primary"
            :disabled="salvandoPerfil"
          >
            {{ salvandoPerfil ? 'Salvando...' : 'Salvar' }}
          </BaseButton>
        </template>
      </BaseModal>

      <BaseModal
        :aberto="modalProrrogacaoAberto"
        :titulo="editandoProrrogacaoId ? 'Editar prorrogação' : 'Adicionar prorrogação'"
        @fechar="fecharModalProrrogacao"
      >
        <form id="form-prorrogacao" class="form-grid" @submit.prevent="salvarProrrogacao">
          <div class="form-group">
            <label for="prorrogacao-tipo">Prazo prorrogado *</label>
            <select id="prorrogacao-tipo" v-model="formProrrogacao.tipo_prazo" required>
              <option value="" disabled>Selecione</option>
              <option v-for="tipo in tiposPrazoProrrogacao" :key="tipo.valor" :value="tipo.valor">
                {{ tipo.rotulo }}
              </option>
            </select>
          </div>

          <div class="form-group">
            <label for="prorrogacao-meses">Quantidade de meses *</label>
            <input
              id="prorrogacao-meses"
              v-model="formProrrogacao.quantidade_meses"
              type="number"
              min="1"
              step="1"
              required
            />
          </div>

          <div class="form-group">
            <label for="prorrogacao-data">Data do pedido *</label>
            <input
              id="prorrogacao-data"
              v-model="formProrrogacao.data_pedido"
              type="date"
              required
            />
          </div>

          <div class="form-group">
            <label for="prorrogacao-resultado">Resultado</label>
            <select id="prorrogacao-resultado" v-model="formProrrogacao.resultado_pedido">
              <option value="">Sem resultado</option>
              <option
                v-for="resultado in resultadosProrrogacao"
                :key="resultado.valor"
                :value="resultado.valor"
              >
                {{ resultado.rotulo }}
              </option>
            </select>
          </div>

          <p v-if="erroProrrogacao" class="aviso-erro span-full">{{ erroProrrogacao }}</p>
        </form>

        <template #rodape>
          <BaseButton
            type="button"
            variant="secondary"
            :disabled="salvandoProrrogacao"
            @click="fecharModalProrrogacao"
          >
            Cancelar
          </BaseButton>
          <BaseButton
            type="submit"
            form="form-prorrogacao"
            variant="primary"
            :disabled="salvandoProrrogacao"
          >
            {{ salvandoProrrogacao ? 'Salvando...' : 'Salvar' }}
          </BaseButton>
        </template>
      </BaseModal>
    </template>
  </DefaultLayout>
</template>

<style scoped>
.aviso-flutuante {
  position: fixed;
  top: 80px;
  right: 24px;
  z-index: 150;
  padding: 12px 16px;
  border-radius: 6px;
  font-size: 0.95rem;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.aviso-flutuante-sucesso {
  background-color: #ecfdf5;
  color: #065f46;
  border: 1px solid #a7f3d0;
}

.aviso-flutuante-erro {
  background-color: #fef2f2;
  color: #b91c1c;
  border: 1px solid #fecaca;
}

.link-voltar {
  margin-bottom: 16px;
  padding: 0;
  border: none;
  background: none;
  color: #1d4ed8;
  font: inherit;
  font-size: 0.9rem;
  cursor: pointer;
}

.link-voltar:hover {
  text-decoration: underline;
}

.link-voltar:focus-visible {
  outline: 2px solid #3b82f6;
  outline-offset: 2px;
  border-radius: 2px;
}

.estado {
  padding: 24px;
  color: #4b5563;
  background-color: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
}

.aviso-erro {
  margin: 0;
  padding: 12px 16px;
  color: #b91c1c;
  background-color: #fef2f2;
  border: 1px solid #fecaca;
  border-radius: 8px;
}

.card {
  margin-bottom: 24px;
  padding: 24px;
  background-color: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
}

.card h2 {
  margin: 0 0 16px 0;
  padding-bottom: 8px;
  font-size: 1.25rem;
  color: #374151;
  border-bottom: 1px solid #e5e7eb;
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
  padding: 0;
  border: none;
}

.perfil-topo {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 24px;
}

.perfil-identidade {
  display: flex;
  align-items: center;
  gap: 16px;
}

.perfil-identidade h1 {
  margin: 0 0 8px 0;
  font-size: 1.8rem;
  color: #111827;
}

.perfil-selos {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
}

.avatar {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 56px;
  height: 56px;
  flex-shrink: 0;
  border-radius: 9999px;
  background-color: #dbeafe;
  color: #1e40af;
  font-size: 1.1rem;
  font-weight: 600;
}

.dados-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px 24px;
  margin: 0;
}

.dados-grid dt,
.marco-dados dt {
  margin-bottom: 2px;
  font-size: 0.8rem;
  font-weight: 500;
  color: #6b7280;
}

.dados-grid dd,
.marco-dados dd {
  margin: 0;
  font-size: 0.95rem;
  color: #111827;
  overflow-wrap: anywhere;
}

.dado-prazo {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
}

.texto-prazo {
  font-size: 0.8rem;
  color: #6b7280;
}

.texto-vazio {
  margin: 0;
  color: #9ca3af;
  font-style: italic;
}

.marcos-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 16px;
}

.marco {
  padding: 16px;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  background-color: #f9fafb;
}

.marco h3 {
  margin: 0 0 12px 0;
  font-size: 1rem;
  color: #374151;
}

.marco-dados {
  display: grid;
  gap: 10px;
  margin: 0;
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

.selo-bolsista {
  padding: 2px 8px;
  border-radius: 9999px;
  border: 1px solid #99f6e4;
  background-color: #f0fdfa;
  color: #115e59;
  font-size: 0.75rem;
  font-weight: 500;
}

.badge {
  display: inline-block;
  padding: 4px 10px;
  border-radius: 9999px;
  font-size: 0.75rem;
  font-weight: 600;
  white-space: nowrap;
}

.badge-neutro {
  background-color: #f3f4f6;
  color: #374151;
}

.status-ativo,
.resultado-deferido {
  background-color: #ecfdf5;
  color: #065f46;
}

.status-trancado,
.resultado-analise {
  background-color: #fffbeb;
  color: #92400e;
}

.status-desligamento,
.resultado-indeferido {
  background-color: #fef2f2;
  color: #b91c1c;
}

.status-desligado {
  background-color: #f3f4f6;
  color: #4b5563;
}

.status-pos-defesa {
  background-color: #eff6ff;
  color: #1e40af;
}

.status-titulado {
  background-color: #f5f3ff;
  color: #5b21b6;
}

.alerta-prazo {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
  flex-shrink: 0;
  border-radius: 9999px;
  font-size: 0.75rem;
  font-weight: 700;
  cursor: help;
}

.prazo-proximo {
  background-color: #fef3c7;
  color: #92400e;
  border: 1px solid #fcd34d;
}

.prazo-vencido {
  background-color: #fee2e2;
  color: #b91c1c;
  border: 1px solid #fca5a5;
}

/* Formulários dentro dos modais (mesmo visual do modal de cadastro) */
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
  align-self: end;
  padding-bottom: 10px;
}

.form-group-checkbox label {
  font-size: 0.9rem;
  color: #374151;
  cursor: pointer;
}

.dica {
  margin: 0;
  font-size: 0.8rem;
  color: #6b7280;
}
</style>
