// Funções que buscam os dados da Central de Alertas.
// TEMPORÁRIO: enquanto as rotas do back-end não existem, devolvem os dados do mock.
// Quando a Elis criar GET /alertas/pendentes e GET /historico-alertas,
// só este arquivo muda (para usar o fetch); a tela continua igual.
import { alertasPendentesMock, historicoAlertasMock } from '../mocks/alertasMock'

// Simula o tempo de resposta do servidor, para a tela mostrar "Carregando...".
function esperar(milissegundos) {
  return new Promise((resolver) => setTimeout(resolver, milissegundos))
}

export async function buscarAlertasPendentes() {
  await esperar(300)
  return structuredClone(alertasPendentesMock)
}

export async function buscarHistoricoAlertas() {
  await esperar(300)
  return structuredClone(historicoAlertasMock)
}
