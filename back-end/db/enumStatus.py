from enum import Enum

class StrEnum(str, Enum):
    """Classe base para Enums baseados em string."""

    def __str__(self) -> str:
        return str(self.value)


# ==========================================
# DISCIPLINAS
# ==========================================
class GrupoPesquisa(StrEnum):
    GRUPO_1 = "GRUPO 1" # Teoria da Computação, Análise de Algoritmos...
    GRUPO_2 = "GRUPO 2" # Metodologia e Técnicas de Computação
    GRUPO_3 = "GRUPO 3" # Sistemas de Computação
    GRUPO_4 = "GRUPO 4" # Outros

class NaturezaDisciplina(StrEnum):
    BASICAS = "BASICAS"
    ELETIVAS = "ELETIVAS"
    TOPICOS_ESPECIAIS = "TOPICOS_ESPECIAIS"
    ESTUDO_DIRIGIDO = "ESTUDO_DIRIGIDO"
    DOCENCIA = "DOCENCIA"


# ==========================================
# HISTORICO_DISCIPLINAS
# ==========================================
class ConceitoHistorico(StrEnum):
    A = "A"
    B = "B"
    C = "C"
    D = "D"


class StatusDisciplina(StrEnum):
    APROVADO = "APROVADO"
    REPROVADO = "REPROVADO"
    PENDENTE = "PENDENTE"
    CANCELADO = "CANCELADO"


# =========================================
# ESTUDANTES
# =========================================

    
class StatusEstudanteEnum(StrEnum):
    ATIVO = "ATIVO"
    TRANCADO = "TRANCADO"
    PROCESSO_DESLIGAMENTO = "PROCESSO DE DESLIGAMENTO"
    DESLIGADO = "DESLIGADO"
    POS_DEFESA = "PÓS DEFESA"
    TITULADO = "TITULADO"




# ==========================================
# ESTAGIOS_DOCENCIA
# ==========================================
class StatusPropostaEstagio(StrEnum):
    SUBMETIDA = "SUBMETIDA"
    APROVADA = "APROVADA"
    PENDENTE = "PENDENTE"
    DISPENSA = "DISPENSA"
    CANCELADO = "CANCELADO"


class StatusRelatorioEstagio(StrEnum):
    SUBMETIDO = "SUBMETIDO"
    APROVADO = "APROVADO"
    PENDENTE = "PENDENTE"


# ==========================================
# PROFICIENCIAS
# ==========================================
class StatusCertificadoProficiencia(StrEnum):
    ENTREGUE = "ENTREGUE"
    PENDENTE = "PENDENTE"
    DISPENSA = "DISPENSA"
    APROVADA = "APROVADA"
    REPROVADA = "REPROVADA"


# ==========================================
# SUBMISSOES_ARTIGOS
# ==========================================
class StatusComprovanteArtigo(StrEnum):
    PUBLICADO = "PUBLICADO"
    SUBMETIDA = "SUBMETIDA"
    DISPENSA = "DISPENSA"
    NEGADO = "NEGADO"


class QualisArtigo(StrEnum):
    A1 = "A1"
    A2 = "A2"
    A3 = "A3"
    A4 = "A4"
    B1 = "B1"
    B2 = "B2"
    B3 = "B3"
    B4 = "B4"
    B5 = "B5"
    C = "C"


class TipoArtigo(StrEnum):
    PERIODICO = "PERIÓDICO"
    EVENTO = "EVENTO"
    CONFERENCIA = "CONFERÊNCIA"
    CAPITULO_LIVRO = "CAPÍTULO DE LIVRO"


class StatusValidacaoColegiadoArtigo(StrEnum):
    SUBMETIDA = "SUBMETIDA"
    APROVADA = "APROVADA"
    PENDENTE = "PENDENTE"
    REPROVADA = "REPROVADA"


# ==========================================
# QUALIFICACOES
# ==========================================
class StatusQualificacao(StrEnum):
    ENTREGUE = "ENTREGUE"
    PENDENTE = "PENDENTE"
    DISPENSA = "DISPENSA"
    REPROVADO = "REPROVADO"


class RetornoQualificacao(StrEnum):
    CADASTROU_BANCA = "Cadastrou Banca"
    SOLICITOU_PRORROGACAO = "Solicitou Prorrogação"


# ==========================================
# DEFESAS
# ==========================================
class StatusDefesa(StrEnum):
    PENDENTE = "PENDENTE"
    DEFENDIDA = "DEFENDIDA"
    CONCLUIDO = "CONCLUIDO"
    EM_HOMOLOGACAO = "EM_HOMOLOGACAO"
    CANCELADO = "CANCELADO"


class RetornoDefesa(StrEnum):
    CADASTROU_BANCA = "Cadastrou Banca"
    SOLICITOU_PRORROGACAO = "Solicitou Prorrogação"


class ConceitoDefesa(StrEnum):
    APROVADO = "APROVADO"
    APROVADO_CONDICIONALMENTE = "APROVADO_CONDICIONALMENTE"
    REPROVADO = "REPROVADO"


class StatusHomologacaoBanca(StrEnum):
    PENDENTE = "PENDENTE"
    SOLICITADA = "SOLICITADA"
    APROVADA_COLEGIADO = "APROVADA_COLEGIADO"


class StatusProcessoDiploma(StrEnum):
    PENDENTE = "PENDENTE"
    DOCUMENTACAO_ENVIADA = "DOCUMENTACAO_ENVIADA"
    PROCESSO_ABERTO = "PROCESSO_ABERTO"


# ==========================================
# PRORROGACOES_HISTORICO
# ==========================================
class TipoPrazoProrrogacao(StrEnum):
    QUALIFICACAO = "QUALIFICACAO"
    DEFESA = "DEFESA"


class ResultadoPedidoProrrogacao(StrEnum):
    DEFERIDO = "DEFERIDO"
    INDEFERIDO = "INDEFERIDO"
    EM_ANALISE = "EM ANÁLISE"


# ==========================================
# HISTORICO_ALERTAS_ENVIADOS
# ==========================================
class CanalAlerta(StrEnum):
    EMAIL = "EMAIL"
    SISTEMA = "SISTEMA"


class StatusEnvioAlerta(StrEnum):
    ENVIADO = "ENVIADO"
    FALHA = "FALHA"


# ==========================================
# USUARIOS E PERFIS
# ==========================================
class StatusContaUsuario(StrEnum):
    ATIVO = "ATIVO"
    INATIVO = "INATIVO"
    BLOQUEADO = "BLOQUEADO"


class NomePerfil(StrEnum):
    ADMIN = "ADMIN"
    SECRETARIA = "SECRETARIA"
    COORDENACAO = "COORDENACAO"
    DISCENTE = "DISCENTE"
