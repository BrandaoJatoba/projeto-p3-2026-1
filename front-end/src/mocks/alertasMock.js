// TEMPORÁRIO: dados de mentira para montar a Central de Alertas
// enquanto as rotas do back-end não existem.
// O formato segue o que foi combinado com a Elis.
// Apagar este arquivo quando o services/alertas.js passar a usar o fetch.

function formatar(data) {
  const ano = data.getFullYear()
  const mes = String(data.getMonth() + 1).padStart(2, '0')
  const dia = String(data.getDate()).padStart(2, '0')
  return `${ano}-${mes}-${dia}`
}

function dataDaqui(dias) {
  const data = new Date()
  data.setDate(data.getDate() + dias)
  return formatar(data)
}

function dataHoraDaqui(dias, hora) {
  return `${dataDaqui(dias)}T${hora}:00`
}

const professores = {
  ada: { id_professor: 1, nome_professor: 'Ada Lovelace', email: 'ada@ic.ufal.br' },
  alan: { id_professor: 2, nome_professor: 'Alan Turing', email: 'alan@ic.ufal.br' },
  donald: { id_professor: 3, nome_professor: 'Donald Knuth', email: 'donald@ic.ufal.br' },
  grace: { id_professor: 4, nome_professor: 'Grace Hopper', email: null },
}

function orientador(professor) {
  return { ...professor, tipo_orientacao: 'ORIENTADOR' }
}

function coorientador(professor) {
  return { ...professor, tipo_orientacao: 'COORIENTADOR' }
}

const tipos = {
  qualificacao: { id_tipo_prazo: 1, nome_prazo: 'Qualificação' },
  defesa: { id_tipo_prazo: 2, nome_prazo: 'Defesa' },
  versaoFinal: { id_tipo_prazo: 3, nome_prazo: 'Versão final' },
  diploma: { id_tipo_prazo: 4, nome_prazo: 'Diploma' },
}

const especificacoes = [
  // Críticos (vencidos ou até 7 dias)
  {
    nome: 'Ana Clara Lima',
    bolsista: true,
    tipo: 'qualificacao',
    dias: -3,
    gatilho: 7,
    orientadores: [orientador(professores.ada)],
  },
  {
    nome: 'Bruno Medeiros',
    bolsista: false,
    tipo: 'defesa',
    dias: 0,
    gatilho: 7,
    orientadores: [orientador(professores.alan), coorientador(professores.donald)],
  },
  {
    nome: 'Camila Ferreira',
    bolsista: true,
    tipo: 'versaoFinal',
    dias: 2,
    gatilho: 7,
    orientadores: [orientador(professores.donald)],
  },
  {
    nome: 'Daniel Souza',
    bolsista: false,
    tipo: 'qualificacao',
    dias: 5,
    gatilho: 7,
    semEmail: true,
    orientadores: [orientador(professores.ada), coorientador(professores.grace)],
  },
  {
    nome: 'Eduarda Nunes',
    bolsista: true,
    tipo: 'diploma',
    dias: 7,
    gatilho: 7,
    orientadores: [orientador(professores.alan)],
  },
  // Atenção (8 a 30 dias)
  {
    nome: 'Felipe Tenório',
    bolsista: false,
    tipo: 'defesa',
    dias: 8,
    gatilho: 30,
    orientadores: [orientador(professores.donald)],
  },
  {
    nome: 'Gabriela Alves',
    bolsista: true,
    tipo: 'qualificacao',
    dias: 15,
    gatilho: 30,
    orientadores: [orientador(professores.ada), coorientador(professores.alan)],
  },
  {
    nome: 'Heitor Ramos',
    bolsista: false,
    tipo: 'versaoFinal',
    dias: 30,
    gatilho: 30,
    orientadores: [orientador(professores.alan)],
  },
  // Preventivos (mais de 30 dias)
  {
    nome: 'Isabela Costa',
    bolsista: true,
    tipo: 'defesa',
    dias: 31,
    gatilho: 60,
    orientadores: [orientador(professores.donald)],
  },
  {
    nome: 'João Pedro Gomes',
    bolsista: false,
    tipo: 'qualificacao',
    dias: 45,
    gatilho: 60,
    orientadores: [orientador(professores.ada)],
  },
  {
    nome: 'Larissa Moura',
    bolsista: true,
    tipo: 'defesa',
    dias: 60,
    gatilho: 60,
    orientadores: [orientador(professores.alan), coorientador(professores.ada)],
  },
  {
    nome: 'Mateus Barbosa',
    bolsista: false,
    tipo: 'qualificacao',
    dias: 90,
    gatilho: 90,
    orientadores: [orientador(professores.donald)],
  },
]

export const alertasPendentesMock = especificacoes.map((e, indice) => {
  const numero = indice + 1
  const matricula = `20251${String(numero).padStart(3, '0')}`
  return {
    id_alerta: numero,
    id_estudante: 100 + numero,
    nome_discente: e.nome,
    matricula,
    email: e.semEmail ? null : `aluno${matricula}@ic.ufal.br`,
    eh_bolsista: e.bolsista,
    ...tipos[e.tipo],
    data_limite: dataDaqui(e.dias),
    dias_restantes: e.dias,
    id_gatilho: numero,
    dias_antecedencia: e.gatilho,
    orientadores: e.orientadores,
  }
})

export const historicoAlertasMock = [
  {
    id_historico: 1,
    id_estudante: 201,
    nome_discente: 'Nicolas Pereira',
    matricula: '20241001',
    nome_prazo: 'Qualificação',
    data_envio: dataHoraDaqui(0, '09:15'),
    status: 'ENVIADO',
    destinatario_email: 'aluno20241001@ic.ufal.br',
    emails_cc: 'ada@ic.ufal.br',
    assunto: 'Prazo de qualificação se aproximando',
    mensagem_erro: null,
  },
  {
    id_historico: 2,
    id_estudante: 202,
    nome_discente: 'Olívia Santos',
    matricula: '20241002',
    nome_prazo: 'Defesa',
    data_envio: dataHoraDaqui(0, '09:16'),
    status: 'ENVIADO',
    destinatario_email: 'aluno20241002@ic.ufal.br',
    emails_cc: 'alan@ic.ufal.br, donald@ic.ufal.br',
    assunto: 'Prazo de defesa se aproximando',
    mensagem_erro: null,
  },
  {
    id_historico: 3,
    id_estudante: 203,
    nome_discente: 'Pedro Henrique Lins',
    matricula: '20241003',
    nome_prazo: 'Versão final',
    data_envio: dataHoraDaqui(0, '09:17'),
    status: 'FALHA',
    destinatario_email: 'aluno20241003@ic.ufal.br',
    emails_cc: 'donald@ic.ufal.br',
    assunto: 'Entrega da versão final',
    mensagem_erro: 'Servidor de e-mail indisponível.',
  },
  {
    id_historico: 4,
    id_estudante: 204,
    nome_discente: 'Rafaela Duarte',
    matricula: '20241004',
    nome_prazo: 'Qualificação',
    data_envio: dataHoraDaqui(-1, '14:30'),
    status: 'ENVIADO',
    destinatario_email: 'aluno20241004@ic.ufal.br',
    emails_cc: 'ada@ic.ufal.br',
    assunto: 'Prazo de qualificação se aproximando',
    mensagem_erro: null,
  },
]
