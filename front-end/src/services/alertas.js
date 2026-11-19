// Funções que buscam e enviam os dados da Central de Alertas.
// TEMPORÁRIO: enquanto as rotas do back-end não existem, usam os dados do mock.
// Quando a Elis criar as rotas (GET /alertas/pendentes, GET /historico-alertas e
// POST /historico-alertas/{id}/reenviar), só este arquivo muda (para usar o fetch);
// a tela continua igual.
import { alertasPendentesMock, historicoAlertasMock } from '../mocks/alertasMock'

// Enquanto for true, a tela mostra o aviso de "dados de exemplo".
// Quando trocar pelo fetch, apagar esta linha (e a pasta mocks).
export const usandoDadosDeExemplo = true

// Simula o tempo de resposta do servidor, para a tela mostrar "Carregando...".
function esperar(milissegundos) {
  return new Promise((resolver) => setTimeout(resolver, milissegundos))
}

function agoraTexto() {
  const agora = new Date()
  const ano = agora.getFullYear()
  const mes = String(agora.getMonth() + 1).padStart(2, '0')
  const dia = String(agora.getDate()).padStart(2, '0')
  const hora = String(agora.getHours()).padStart(2, '0')
  const minuto = String(agora.getMinutes()).padStart(2, '0')
  return `${ano}-${mes}-${dia}T${hora}:${minuto}:00`
}

export async function buscarAlertasPendentes() {
  await esperar(300)
  return structuredClone(alertasPendentesMock)
}

export async function buscarHistoricoAlertas() {
  await esperar(300)
  return structuredClone(historicoAlertasMock)
}

// Simula o reenvio de um alerta que falhou: ele passa a constar como enviado agora.
// (Só na memória: depois de recarregar a página, volta ao que está no mock.)
export async function reenviarAlerta(idHistorico) {
  await esperar(500)
  const envio = historicoAlertasMock.find((h) => h.id_historico === idHistorico)
  if (!envio) throw new Error('Envio não encontrado.')
  envio.status = 'ENVIADO'
  envio.mensagem_erro = null
  envio.data_envio = agoraTexto()
  return structuredClone(envio)
}
