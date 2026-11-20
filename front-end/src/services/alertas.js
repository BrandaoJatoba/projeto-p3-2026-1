// Funções que buscam os dados da Central de Alertas.
// - Pendentes: rota real do back-end (GET /alertas/pendentes).
// - Histórico: TEMPORÁRIO, ainda usa o mock, porque a rota GET /alertas/historico
//   ainda não está na dev. Quando ela chegar, só este arquivo muda.
import { useAuthStore } from '../stores/auth'
import { historicoAlertasMock } from '../mocks/alertasMock'

const api = 'http://localhost:8000'

// Enquanto for true, a tela avisa que o histórico usa dados de exemplo.
// Quando o histórico passar a usar o fetch, apagar esta linha (e a pasta mocks).
export const historicoDeExemplo = true

function cabecalho() {
  const authStore = useAuthStore()
  return { Authorization: `Bearer ${authStore.token}` }
}

function mensagemPorStatus(status) {
  if (status === 401) return 'Sua sessão expirou. Saia e entre de novo.'
  if (status === 403) return 'Você não tem permissão para ver os alertas.'
  return 'Não foi possível carregar os alertas. Tente de novo em instantes.'
}

// dataReferencia (opcional, "AAAA-MM-DD"): calcula os alertas como se fosse outro dia.
// Serve para testes. A tela chama sem data, e aí o back usa o dia de hoje.
export async function buscarAlertasPendentes(dataReferencia) {
  const parametros = dataReferencia ? `?data_referencia=${dataReferencia}` : ''

  let resposta
  try {
    resposta = await fetch(`${api}/alertas/pendentes${parametros}`, { headers: cabecalho() })
  } catch {
    throw new Error('Não foi possível conectar ao servidor.')
  }

  if (!resposta.ok) throw new Error(mensagemPorStatus(resposta.status))

  const dados = await resposta.json()
  return Array.isArray(dados) ? dados : []
}

// ---------- Histórico (TEMPORÁRIO: mock) ----------

// Simula o tempo de resposta do servidor, para a tela mostrar "Carregando...".
function esperar(milissegundos) {
  return new Promise((resolver) => setTimeout(resolver, milissegundos))
}

export async function buscarHistoricoAlertas() {
  await esperar(300)
  return structuredClone(historicoAlertasMock)
}
