// Funções que conversam com o back-end da Central de Alertas.
// - GET  /alertas/pendentes                    → alertas a enviar
// - GET  /historico-alertas                    → envios já feitos (paginado)
// - POST /historico-alertas/{id}/reenviar      → reenvia um envio que falhou
import { useAuthStore } from '../stores/auth'

const api = 'http://localhost:8000'

// O máximo que a rota do histórico aceita por vez.
const LIMITE_HISTORICO = 200

function cabecalho() {
  const authStore = useAuthStore()
  return { Authorization: `Bearer ${authStore.token}` }
}

// Data de hoje no fuso do computador, no formato "AAAA-MM-DD".
function hojeTexto() {
  const hoje = new Date()
  const ano = hoje.getFullYear()
  const mes = String(hoje.getMonth() + 1).padStart(2, '0')
  const dia = String(hoje.getDate()).padStart(2, '0')
  return `${ano}-${mes}-${dia}`
}

async function lerDetalhe(resposta) {
  try {
    const dados = await resposta.json()
    if (typeof dados.detail === 'string') return dados.detail
  } catch {
    // A resposta não veio em JSON.
  }
  return ''
}

// Faz a chamada e transforma qualquer problema numa mensagem em português.
async function requisitar(caminho, { metodo = 'GET', mensagemPadrao }) {
  let resposta
  try {
    resposta = await fetch(`${api}${caminho}`, { method: metodo, headers: cabecalho() })
  } catch {
    throw new Error('Não foi possível conectar ao servidor.')
  }

  if (!resposta.ok) {
    if (resposta.status === 401) throw new Error('Sua sessão expirou. Saia e entre de novo.')
    if (resposta.status === 403) {
      throw new Error('Você não tem permissão para usar a Central de Alertas.')
    }
    const detalhe = await lerDetalhe(resposta)
    throw new Error(detalhe || mensagemPadrao)
  }

  return resposta.json()
}

// dataReferencia (opcional, "AAAA-MM-DD"): calcula os alertas como se fosse outro dia.
// Serve para testes. A tela chama sem data, e aí o back usa o dia de hoje.
export async function buscarAlertasPendentes(dataReferencia) {
  const parametros = dataReferencia ? `?data_referencia=${dataReferencia}` : ''
  const dados = await requisitar(`/alertas/pendentes${parametros}`, {
    mensagemPadrao: 'Não foi possível carregar os alertas. Tente de novo em instantes.',
  })
  return Array.isArray(dados) ? dados : []
}

// Os envios mais recentes primeiro. Devolve a lista e o total que existe no banco.
export async function buscarHistoricoAlertas() {
  const dados = await requisitar(`/historico-alertas?limit=${LIMITE_HISTORICO}`, {
    mensagemPadrao: 'Não foi possível carregar o histórico de envios.',
  })
  return {
    itens: Array.isArray(dados?.itens) ? dados.itens : [],
    total: dados?.total ?? 0,
  }
}

// Só precisa do número: pede 1 item e usa o "total" da resposta.
export async function contarEnviadosHoje() {
  const hoje = hojeTexto()
  const dados = await requisitar(
    `/historico-alertas?status_envio=ENVIADO&data_inicio=${hoje}&data_fim=${hoje}&limit=1`,
    { mensagemPadrao: 'Não foi possível contar os envios de hoje.' },
  )
  return dados?.total ?? 0
}

// Devolve o registro atualizado (sem nome do discente, matrícula e prazo).
// Se falhar de novo, o back devolve o registro ainda com status FALHA.
export async function reenviarAlerta(idHistoricoAlerta) {
  return requisitar(`/historico-alertas/${idHistoricoAlerta}/reenviar`, {
    metodo: 'POST',
    mensagemPadrao: 'Não foi possível reenviar o alerta. Tente de novo.',
  })
}
