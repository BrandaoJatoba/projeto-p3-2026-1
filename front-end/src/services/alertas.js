// Funções que conversam com o back-end da Central de Alertas.
// - GET  /alertas/pendentes                    → alertas a enviar
// - POST /alertas/minutas/preview              → monta os e-mails (não envia nada)
// - POST /alertas/disparar/individual          → envia um e-mail e grava no histórico
// - GET  /configuracoes/gatilhos/{id}          → gatilho com o modelo do texto (template)
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
// - corpo: dados enviados em JSON (só nas chamadas POST/PUT).
// - mensagensPorStatus: textos próprios para alguns códigos, ex.: { 409: '...' }.
async function requisitar(
  caminho,
  { metodo = 'GET', corpo, mensagemPadrao, mensagensPorStatus = {} },
) {
  const opcoes = { method: metodo, headers: cabecalho() }
  if (corpo !== undefined) {
    opcoes.headers = { ...opcoes.headers, 'Content-Type': 'application/json' }
    opcoes.body = JSON.stringify(corpo)
  }

  let resposta
  try {
    resposta = await fetch(`${api}${caminho}`, opcoes)
  } catch {
    throw new Error('Não foi possível conectar ao servidor.')
  }

  if (!resposta.ok) {
    if (resposta.status === 401) throw new Error('Sua sessão expirou. Saia e entre de novo.')
    if (resposta.status === 403) {
      throw new Error('Você não tem permissão para usar a Central de Alertas.')
    }
    if (mensagensPorStatus[resposta.status]) {
      throw new Error(mensagensPorStatus[resposta.status])
    }
    const detalhe = await lerDetalhe(resposta)
    throw new Error(detalhe || mensagemPadrao)
  }

  return resposta.json()
}

// ---------- Pendentes ----------

// dataReferencia (opcional, "AAAA-MM-DD"): calcula os alertas como se fosse outro dia.
// Serve para testes. A tela chama sem data, e aí o back usa o dia de hoje.
export async function buscarAlertasPendentes(dataReferencia) {
  const parametros = dataReferencia ? `?data_referencia=${dataReferencia}` : ''
  const dados = await requisitar(`/alertas/pendentes${parametros}`, {
    mensagemPadrao: 'Não foi possível carregar os alertas. Tente de novo em instantes.',
  })
  return Array.isArray(dados) ? dados : []
}

// ---------- Minutas e envio ----------

// Gatilho com o modelo do texto (mensagem_template), que pode vir vazio.
export async function buscarGatilho(idGatilho) {
  return requisitar(`/configuracoes/gatilhos/${idGatilho}`, {
    mensagemPadrao: 'Não foi possível carregar o modelo do e-mail.',
  })
}

// itens: [{ id_estudante, id_gatilho }]
// templateCustomizado (opcional): o miolo do e-mail com variáveis, ex.: "Seu prazo de {nome_prazo}...".
// O back acrescenta a saudação e a assinatura e preenche as variáveis. Não envia nem grava nada.
// Devolve { minutas: [...], ignorados: [...] }.
export async function gerarPreviewMinutas(itens, templateCustomizado) {
  const corpo = {
    itens: itens.map(({ id_estudante, id_gatilho }) => ({ id_estudante, id_gatilho })),
  }
  if (templateCustomizado != null) corpo.template_customizado = templateCustomizado

  const dados = await requisitar('/alertas/minutas/preview', {
    metodo: 'POST',
    corpo,
    mensagemPadrao: 'Não foi possível montar a prévia do e-mail.',
  })
  return {
    minutas: Array.isArray(dados?.minutas) ? dados.minutas : [],
    ignorados: Array.isArray(dados?.ignorados) ? dados.ignorados : [],
  }
}

// dados: { id_estudante, id_gatilho, assunto, corpo_mensagem,
//          email_destino?, cc_adicionais?, ignorar_cc_ids? }
// ATENÇÃO: o corpo_mensagem vai exatamente como está. O back NÃO preenche variáveis
// nem acrescenta saudação, então mande o texto já pronto (o "corpo" do preview).
// Devolve o registro do histórico, com status_envio ENVIADO ou FALHA.
export async function dispararIndividual(dados) {
  return requisitar('/alertas/disparar/individual', {
    metodo: 'POST',
    corpo: dados,
    mensagemPadrao: 'Não foi possível enviar o e-mail.',
    mensagensPorStatus: {
      404: 'Discente ou gatilho não encontrado.',
      409: 'Este alerta já foi enviado para o discente.',
      422: 'Dados inválidos para o envio. Confira o destinatário e o texto.',
    },
  })
}

// ---------- Histórico ----------

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
