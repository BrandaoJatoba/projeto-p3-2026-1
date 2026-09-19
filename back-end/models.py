from sqlalchemy import Column, Integer, String, Date, Boolean, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship, Mapped, mapped_column
from database import Base

class Usuario(Base): 
    """
    Tabela de autenticação principal. Armazena credenciais de login, status da conta e metadados de acesso de cada usuário.
    """
    
    __tablename__ = "usuarios"

    id_usuario = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(100), unique=True, nullable=False)
    senha_hash = Column(String(255), nullable=False)
    status_conta = Column(String(20), nullable=False, default="ATIVO")
    data_ultimo_login = Column(DateTime, nullable=True)
    data_criacao = Column(DateTime, server_default=func.now())

class UsuarioPerfil(Base):
    
    """
    Tabela intermediária associativa (N:N) que vincula cada usuário a um ou mais perfis de acesso (RBAC).
    """

    __tablename__ = "usuarios_perfis"
    
    id_usuario = Column(Integer, ForeignKey("usuarios.id_usuario"), primary_key=True)
    id_perfil = Column(Integer, ForeignKey("perfis.id_perfil"), primary_key=True)

class Professor(Base):
    
    """
    Registro dos professores do programa, atuando como orientadores de discentes ou supervisores em estágios de docência.
    """

    __tablename__ = "professores"

    id_professor = Column(Integer, primary_key=True, autoincrement=True)
    nome_professor = Column(String(100), nullable=False)

class Disciplina(Base):
    
    """
    Catálogo de disciplinas ofertadas pelo programa de pós-graduação,
    classificadas por grupo e carga de créditos.
    """

    __tablename__ = "disciplinas"

    id_disciplina = Column(Integer, primary_key=True, autoincrement=True)
    codigo_disciplina = Column(String(10), nullable=False)
    nome_disciplina = Column(String(100), nullable=False)
    grupo_disciplina = Column(String(30), nullable=False)
    creditos = Column(Integer, nullable=False)

class SemestreLetivo(Base):
    
    """
    Mapeamento dos períodos acadêmicos (ex: 2026.1), registrando datas
    efetivas de início, término e contagem de dias letivos.
    """

    __tablename__ = "semestres_letivos"

    id_semestre = Column(Integer, primary_key=True, autoincrement=True)
    codigo_semestre = Column(String(6), unique=True, nullable=False)
    data_inicio_real = Column(Date)
    data_fim_real = Column(Date)
    dias_letivos = Column(Integer)

class SuspensaoCalendario(Base):
    
    """
    Registro de paralisações ou suspensões de calendário (greves, prorrogativas)
    que impactam no cálculo de contagem de prazos acadêmicos.
    """

    __tablename__ = "suspensoes_calendario"

    id_suspensao = Column(Integer, primary_key=True, autoincrement=True)
    id_semestre = Column(Integer, ForeignKey("semestres_letivos.id_semestre"), nullable=False)
    motivo = Column(String(100))
    data_inicio_suspensao = Column(Date, nullable=False)
    data_fim_suspensao = Column(Date, nullable=True)
    dias_suspensos = Column(Integer, nullable=True)

class Estudante(Base):
    
    """
    Cadastro central dos discentes do programa contendo informações acadêmicas,
    vínculo de orientação, status de bolsa e prazo limite do SIGAA.
    """

    __tablename__ = "estudantes"

    id_estudante = Column(Integer, primary_key=True, autoincrement=True)
    matricula = Column(String(20), unique=True, nullable=False)
    nome_discente = Column(String(100), nullable=False)
    status_atual = Column(String(30), nullable=False, default="ATIVO")
    id_semestre = Column(Integer, ForeignKey("semestres_letivos.id_semestre"), nullable=False)
    id_orientador = Column(Integer, ForeignKey("professores.id_professor"), nullable=True)
    eh_bolsista = Column(Boolean, default=False)
    prazo_conclusao_sigaa = Column(Date, nullable=True)

class HistoricoDisciplina(Base):
    
    """
    Registro de disciplinas cursadas pelo estudante em cada semestre,
    armazenando o conceito obtido, status e créditos integralizados.
    """

    __tablename__ = "historico_disciplinas"

    id_historico = Column(Integer, primary_key=True, autoincrement=True)
    id_estudante = Column(Integer, ForeignKey("estudantes.id_estudante"), nullable=False)
    id_disciplina = Column(Integer, ForeignKey("disciplinas.id_disciplina"), nullable=False)
    id_semestre = Column(Integer, ForeignKey("semestres_letivos.id_semestre"), nullable=False)
    conceito = Column(String(5))
    status_disciplina = Column(String(20))
    creditos_integralizados = Column(Integer)

class EstagioDocencia(Base):
    
    """
    Acompanhamento das atividades de estágio docência obrigatório, controlando o status da proposta inicial e a entrega do relatório final.
    """

    __tablename__ = "estagios_docencia"

    id_estagio = Column(Integer, primary_key=True, autoincrement=True)
    id_estudante = Column(Integer, ForeignKey("estudantes.id_estudante"), nullable=False)
    id_professor_supervisor = Column(Integer, ForeignKey("professores.id_professor"), nullable=False)
    id_disciplina = Column(Integer, ForeignKey("disciplinas.id_disciplina"), nullable=False)
    id_semestre = Column(Integer, ForeignKey("semestres_letivos.id_semestre"), nullable=False)
    status_proposta = Column(String(20))
    data_entrega_proposta = Column(Date)
    status_relatorio = Column(String(20))
    data_entrega_relatorio = Column(Date)

class Proficiencia(Base):
    
    """
    Controle da comprovação de proficiência em língua estrangeira exigida
    pelo programa de pós-graduação.
    """

    __tablename__ = "proficiencias"

    id_proficiencia = Column(Integer, primary_key=True, autoincrement=True)
    id_estudante = Column(Integer, ForeignKey("estudantes.id_estudante"), nullable=False)
    status_certificado = Column(String(20))
    data_entrega_certificado = Column(Date)
    consolidada_sigaa = Column(Boolean, default=False)

class SubmissaoArtigo(Base):
    
    """
    Registro das submissões de artigos acadêmicos pelos alunos,
    armazenando Qualis, tipo de veículo e validação do colegiado.
    """

    __tablename__ = "submissoes_artigos"

    id_artigo = Column(Integer, primary_key=True, autoincrement=True)
    titulo = Column(String(270), nullable=False)
    id_estudante = Column(Integer, ForeignKey("estudantes.id_estudante"), nullable=False)
    status_comprovante = Column(String(20))
    data_entrega = Column(Date)
    qualis = Column(String(2))
    tipo = Column(String(10))
    status_validacao_colegiado = Column(String(20))

class Dissertacao(Base):
    
    """
    Entidade central de acompanhamento da dissertação do mestrando,
    relacionando o estudante ao projeto e marcando o início da contagem dos prazos.
    """

    __tablename__ = "dissertacoes"

    id_dissertacao = Column(Integer, primary_key=True, autoincrement=True)
    id_estudante = Column(Integer, ForeignKey("estudantes.id_estudante"), unique=True, nullable=False)
    titulo = Column(String(255), nullable=True)
    data_inicio = Column(Date, nullable=False)

class Qualificacao(Base):
    
    """
    Acompanhamento do exame de qualificação da dissertação, registrando
    prazos limites, número de tentativas e resultado final da banca.
    """

    __tablename__ = "qualificacoes"

    id_qualificacao = Column(Integer, primary_key=True, autoincrement=True)
    id_dissertacao = Column(Integer, ForeignKey("dissertacoes.id_dissertacao"), nullable=False)
    prazo_maximo_qualificacao = Column(Date, nullable=False)
    status_qualificacao = Column(String(20))
    retorno_qualificacao = Column(String(30))
    tentativa = Column(Integer, default=1)
    data_realizacao = Column(Date, nullable=True)

class Defesa(Base):
    
    """
    Gerenciamento do rito final de defesa da dissertação, prevendo homologação
    de banca, prazos para versão final com correções e conceito obtido.
    """

    __tablename__ = "defesas"

    id_defesa = Column(Integer, primary_key=True, autoincrement=True)
    id_dissertacao = Column(Integer, ForeignKey("dissertacoes.id_dissertacao"), nullable=False)
    prazo_maximo_defesa = Column(Date, nullable=False)
    prazo_solicitacao_homologacao_banca = Column(Date)
    status_defesa = Column(String(20))
    retorno_defesa = Column(String(30))
    conceito_defesa = Column(String(30))
    prazo_versao_final = Column(Date)
    data_realizacao = Column(Date, nullable=True)

class ProrrogacaoHistorico(Base):
    
    """
    Histórico de solicitações de extensão de prazos de qualificação ou defesa
    aprovadas ou indeferidas pelo colegiado.
    """

    __tablename__ = "prorrogacoes_historico"

    id_prorrogacao = Column(Integer, primary_key=True, autoincrement=True)
    id_estudante = Column(Integer, ForeignKey("estudantes.id_estudante"), nullable=False)
    tipo_prazo = Column(String(15))
    quantidade_meses = Column(Integer)
    data_pedido = Column(Date)
    resultado_pedido = Column(String(15))

class ConfiguracaoAlerta(Base):

    """
    Parâmetros configuráveis pelo sistema para envio de alertas preventivos
    conforme a proximidade do vencimento de prazos regimentais.
    """
    
    __tablename__ = "configuracoes_alertas"

    id_config = Column(Integer, primary_key=True, autoincrement=True)
    tipo_prazo = Column(String(30))
    dias_alerta_1 = Column(Integer, default=90)
    dias_alerta_2 = Column(Integer, default=30)
    dias_alerta_3 = Column(Integer, default=0)

class Perfil(Base):
    
    """
    Catálogo de papéis de acesso (ADMIN, SECRETARIA, COORDENACAO, DISCENTE) utilizados para controle de permissões no sistema (RBAC).
    """
    
    __tablename__ = "perfis"

    id_perfil = Column(Integer, primary_key=True, autoincrement=True)
    nome_perfil = Column(String(30), unique=True, nullable=False)
    descricao = Column(String(150), nullable=True)

class SessionRefreshToken(Base):
    
    """
    Controle e rastreamento de refresh tokens emitidos para persistência
    de sessões JWT ativas por usuário e dispositivo.
    """

    __tablename__ = "sessions_refresh_tokens"

    id_token = Column(Integer, primary_key=True, autoincrement=True)
    id_usuario = Column(Integer, ForeignKey("usuarios.id_usuario"), nullable=False)
    refresh_token = Column(String(512), unique=True, nullable=False)
    dispositivo_info = Column(String(255), nullable=True)
    data_expiracao = Column(DateTime, nullable=False)
    revogado = Column(Boolean, default=False)