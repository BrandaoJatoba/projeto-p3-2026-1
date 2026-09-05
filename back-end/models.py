from sqlalchemy import Column, Integer, String, Date, Boolean, ForeignKey, DateTime, func
from sqlalchemy.orm import relationship, Mapped, mapped_column
from database import Base

class Professor(Base):

    __tablename__ = "professores"

    id_professor = Column(Integer, primary_key=True, autoincrement=True)
    nome_professor = Column(String(100), nullable=False)

class Disciplina(Base):

    __tablename__ = "disciplinas"

    id_disciplina = Column(Integer, primary_key=True, autoincrement=True)
    codigo_disciplina = Column(String(10), nullable=False)
    nome_disciplina = Column(String(100), nullable=False)
    grupo_disciplina = Column(String(30), nullable=False)
    creditos = Column(Integer, nullable=False)

class SemestreLetivo(Base):

    __tablename__ = "semestres_letivos"

    id_semestre = Column(Integer, primary_key=True, autoincrement=True)
    codigo_semestre = Column(String(6), unique=True, nullable=False)
    data_inicio_real = Column(Date)
    data_fim_real = Column(Date)
    dias_letivos = Column(Integer)

class SuspensaoCalendario(Base):

    __tablename__ = "suspensoes_calendario"

    id_suspensao = Column(Integer, primary_key=True, autoincrement=True)
    id_semestre = Column(Integer, ForeignKey("semestres_letivos.id_semestre"), nullable=False)
    motivo = Column(String(100))
    data_inicio_suspensao = Column(Date, nullable=False)
    data_fim_suspensao = Column(Date, nullable=True)
    dias_suspensos = Column(Integer, nullable=True)

class Estudante(Base):

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

    __tablename__ = "historico_disciplinas"

    id_historico = Column(Integer, primary_key=True, autoincrement=True)
    id_estudante = Column(Integer, ForeignKey("estudantes.id_estudante"), nullable=False)
    id_disciplina = Column(Integer, ForeignKey("disciplinas.id_disciplina"), nullable=False)
    id_semestre = Column(Integer, ForeignKey("semestres_letivos.id_semestre"), nullable=False)
    conceito = Column(String(5))
    status_disciplina = Column(String(20))
    creditos_integralizados = Column(Integer)

class EstagioDocencia(Base):

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

    __tablename__ = "proficiencias"

    id_proficiencia = Column(Integer, primary_key=True, autoincrement=True)
    id_estudante = Column(Integer, ForeignKey("estudantes.id_estudante"), nullable=False)
    status_certificado = Column(String(20))
    data_entrega_certificado = Column(Date)
    consolidada_sigaa = Column(Boolean, default=False)

class SubmissaoArtigo(Base):

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

    __tablename__ = "dissertacoes"

    id_dissertacao = Column(Integer, primary_key=True, autoincrement=True)
    id_estudante = Column(Integer, ForeignKey("estudantes.id_estudante"), unique=True, nullable=False)
    titulo = Column(String(255), nullable=True)
    data_inicio = Column(Date, nullable=False)

class Qualificacao(Base):

    __tablename__ = "qualificacoes"

    id_qualificacao = Column(Integer, primary_key=True, autoincrement=True)
    id_dissertacao = Column(Integer, ForeignKey("dissertacoes.id_dissertacao"), nullable=False)
    prazo_maximo_qualificacao = Column(Date, nullable=False)
    status_qualificacao = Column(String(20))
    retorno_qualificacao = Column(String(30))
    tentativa = Column(Integer, default=1)
    data_realizacao = Column(Date, nullable=True)

class Defesa(Base):

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

    __tablename__ = "prorrogacoes_historico"

    id_prorrogacao = Column(Integer, primary_key=True, autoincrement=True)
    id_estudante = Column(Integer, ForeignKey("estudantes.id_estudante"), nullable=False)
    tipo_prazo = Column(String(15))
    quantidade_meses = Column(Integer)
    data_pedido = Column(Date)
    resultado_pedido = Column(String(15))

class ConfiguracaoAlerta(Base):

    __tablename__ = "configuracoes_alertas"

    id_config = Column(Integer, primary_key=True, autoincrement=True)
    tipo_prazo = Column(String(30))
    dias_alerta_1 = Column(Integer, default=90)
    dias_alerta_2 = Column(Integer, default=30)
    dias_alerta_3 = Column(Integer, default=0)

class Usuario(Base):

    __tablename__ = "usuarios"

    id_usuario = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(100), unique=True, nullable=False)
    senha_hash = Column(String(255), nullable=False)
    status_conta = Column(String(20), nullable=False, default="ATIVO")
    data_ultimo_login = Column(DateTime, nullable=True)
    data_criacao = Column(DateTime, server_default=func.now())

class Perfil(Base):
    
    __tablename__ = "perfis"

    id_perfil = Column(Integer, primary_key=True, autoincrement=True)
    nome_perfil = Column(String(30), unique=True, nullable=False)
    descricao = Column(String(150), nullable=True)

class UsuarioPerfil(Base):

    __tablename__ = "usuarios_perfis"
    
    id_usuario = Column(Integer, ForeignKey("usuarios.id_usuario"), primary_key=True)
    id_perfil = Column(Integer, ForeignKey("perfis.id_perfil"), primary_key=True)

class SessionRefreshToken(Base):

    __tablename__ = "sessions_refresh_tokens"

    id_token = Column(Integer, primary_key=True, autoincrement=True)
    id_usuario = Column(Integer, ForeignKey("usuarios.id_usuario"), nullable=False)
    refresh_token = Column(String(512), unique=True, nullable=False)
    dispositivo_info = Column(String(255), nullable=True)
    data_expiracao = Column(DateTime, nullable=False)
    revogado = Column(Boolean, default=False)