// Funções da tela de importação de discentes (arquivo CSV do SIGAA).
// - GET  /configuracoes/semestres                → semestres letivos (período de ingresso)
// - POST /importacao/discentes-basico/preview    → analisa o arquivo (não grava nada)
import { useAuthStore } from '../stores/auth'

const api = 'http://localhost:8000'

function cabecalho() {
  const authStore = useAuthStore()
  return { Authorization: `Bearer ${authStore.token}` }
}

async function lerDetalhe(resposta) {
  try {
    const dados = await resposta.json()
    return typeof dados?.detail === 'string' ? dados.detail : ''
  } catch {
    return '' // a resposta não veio em JSON
  }
}

export async function buscarSemestres() {
  let resposta
  try {
    resposta = await fetch(`${api}/configuracoes/semestres`, { headers: cabecalho() })
  } catch {
    throw new Error('Não foi possível conectar ao servidor.')
  }

  if (resposta.status === 401) throw new Error('Sua sessão expirou. Saia e entre de novo.')
  if (resposta.status === 403) throw new Error('Você não tem permissão para importar discentes.')
  if (!resposta.ok) throw new Error('Não foi possível carregar os semestres.')

  const dados = await resposta.json()
  return Array.isArray(dados) ? dados : []
}

// Manda o arquivo e o semestre para o back analisar. Nada é gravado no banco nesta etapa.
// Devolve as listas novos, ja_cadastrados e com_erro (e os totais).
export async function analisarArquivoDiscentes(arquivo, idSemestre) {
  // FormData = o "pacote" do multipart/form-data, que leva o arquivo e os campos juntos.
  const pacote = new FormData()
  pacote.append('arquivo', arquivo)
  pacote.append('id_semestre', String(idSemestre))

  let resposta
  try {
    // Sem 'Content-Type' de propósito: o navegador monta o multipart/form-data sozinho.
    resposta = await fetch(`${api}/importacao/discentes-basico/preview`, {
      method: 'POST',
      headers: cabecalho(),
      body: pacote,
    })
  } catch {
    throw new Error('Não foi possível conectar ao servidor. Confira sua conexão e tente de novo.')
  }

  if (resposta.ok) return resposta.json()

  const detalhe = await lerDetalhe(resposta)
  if (resposta.status === 401) throw new Error('Sua sessão expirou. Saia e entre de novo.')
  if (resposta.status === 403) throw new Error('Você não tem permissão para importar discentes.')
  if (resposta.status === 404) {
    // "Not Found" é a resposta padrão do FastAPI quando a rota não existe.
    if (!detalhe || detalhe === 'Not Found') {
      throw new Error('A análise de arquivos ainda não está disponível no servidor.')
    }
    throw new Error(detalhe) // ex.: semestre não encontrado
  }
  if (resposta.status === 413) throw new Error('O arquivo é grande demais para ser enviado.')
  if (resposta.status === 422) {
    throw new Error(
      detalhe ||
        'O arquivo ou o semestre não foram aceitos. Confira se o arquivo é o CSV exportado do SIGAA.',
    )
  }
  throw new Error(detalhe || 'Não foi possível analisar o arquivo. Tente de novo em instantes.')
}
