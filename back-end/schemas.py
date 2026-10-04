from datetime import date
from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
import db.enumStatus as enumStatus


class SemestreCriacao(BaseModel):
    codigo_semestre: str = Field(max_length=6)
    data_inicio_real: date
    data_fim_real: date
    dias_letivos: int

class SemestreAtualizacao(BaseModel):
    data_inicio_real: date
    data_fim_real: date
    dias_letivos: int

class SemestreResposta(BaseModel):

    model_config = ConfigDict(from_attributes=True)

    id_semestre: int
    codigo_semestre: str
    data_inicio_real: Optional[date]
    data_fim_real: Optional[date]
    dias_letivos: Optional[int]

# Schema Base com os campos comuns
class SuspensaoCalendarioBase(BaseModel):
    motivo: Optional[str] = Field(None, max_length=100, description="Motivo da suspensão (ex: Greve, Pandemia)")
    data_inicio_suspensao: date = Field(..., description="Data de início da suspensão")
    data_fim_suspensao: Optional[date] = Field(None, description="Data de término da suspensão")
    dias_suspensos: Optional[int] = Field(None, description="Quantidade de dias letivos suspensos")

# Schema para criação (POST) - Exige o id_semestre
class SuspensaoCalendarioCreate(SuspensaoCalendarioBase):
    id_semestre: int = Field(..., description="ID do semestre letivo associado")

# Schema para atualização (PUT/PATCH) - Torna todos os campos opcionais
class SuspensaoCalendarioUpdate(BaseModel):
    id_semestre: Optional[int] = None
    motivo: Optional[str] = Field(None, max_length=100)
    data_inicio_suspensao: Optional[date] = None
    data_fim_suspensao: Optional[date] = None
    dias_suspensos: Optional[int] = None

# Schema de resposta (GET ou retorno de POST/PUT) - Inclui o ID gerado pelo banco
class SuspensaoCalendarioResponse(SuspensaoCalendarioBase):
    id_suspensao: int
    id_semestre: int

    # Configuração necessária para o Pydantic ler objetos do SQLAlchemy
    model_config = ConfigDict(from_attributes=True)

from pydantic import BaseModel, Field, ConfigDict


# Schema base com os campos comuns
class TipoPrazoBase(BaseModel):
    codigo_prazo: str = Field(..., max_length=50, example="QUALIFICACAO")
    nome_prazo: str = Field(..., max_length=100, example="Exame de Qualificação")
    descricao: Optional[str] = Field(None, max_length=255, example="Prazo para apresentação da qualificação")


# Schema para criação (POST)
class TipoPrazoCreate(TipoPrazoBase):
    pass


# Schema para atualização (PUT)
class TipoPrazoUpdate(BaseModel):
    codigo_prazo: Optional[str] = Field(None, max_length=50)
    nome_prazo: Optional[str] = Field(None, max_length=100)
    descricao: Optional[str] = Field(None, max_length=255)


# Schema para resposta/leitura (GET/POST/PUT)
class TipoPrazoResponse(TipoPrazoBase):
    id_tipo_prazo: int

    model_config = ConfigDict(from_attributes=True)

# ==========================================
# Schemas para GatilhoAlerta
# ==========================================

class GatilhoAlertaBase(BaseModel):
    id_tipo_prazo: int = Field(..., example=1)
    dias_antecedencia: int = Field(..., gt=0, example=30)
    mensagem_template: Optional[str] = Field(None, example="Atenção: Faltam {dias} dias para a sua qualificação.")
    ativo: bool = Field(default=True)

class GatilhoAlertaCreate(GatilhoAlertaBase):
    pass

class GatilhoAlertaUpdate(BaseModel):
    dias_antecedencia: Optional[int] = Field(None, gt=0)
    mensagem_template: Optional[str] = None
    ativo: Optional[bool] = None

class GatilhoAlertaResponse(GatilhoAlertaBase):
    id_gatilho: int

    model_config = ConfigDict(from_attributes=True)

# ==========================================
# SCHEMAS DE DISCIPLINA
# ==========================================

class DisciplinaBase(BaseModel):
    """Atributos comuns compartilhados entre schemas de disciplina."""
    codigo_disciplina: str = Field(
        ..., 
        max_length=20, 
        description="Código identificador da disciplina (ex: PPGI 001)",
        examples=["PPGI 001"]
    )
    nome_disciplina: str = Field(
        ..., 
        max_length=100, 
        description="Nome da disciplina",
        examples=["Teoria da Computação"]
    )
    grupo_disciplina: enumStatus.GrupoDisciplina = Field(
        ..., 
        description="Grupo ao qual a disciplina pertence"
    )
    creditos: int = Field(
        ..., 
        gt=0, 
        description="Quantidade de créditos (deve ser maior que zero)",
        examples=[4]
    )


class DisciplinaCreate(DisciplinaBase):
    """Schema para criação de disciplina (dados enviados no corpo do POST)."""
    pass


class DisciplinaUpdate(BaseModel):
    """Schema para atualização parcial de disciplina (dados do PATCH/PUT)."""
    codigo_disciplina: Optional[str] = Field(None, max_length=20)
    nome_disciplina: Optional[str] = Field(None, max_length=100)
    grupo_disciplina: Optional[enumStatus.GrupoDisciplina] = None
    creditos: Optional[int] = Field(None, gt=0)


class DisciplinaResponse(DisciplinaBase):
    """Schema de resposta retornado pela API para o cliente (inclui o ID)."""
    id_disciplina: int

    model_config = ConfigDict(from_attributes=True)

# ==========================================
# SCHEMAS DE ESTÁGIO DOCÊNCIA
# ==========================================

class EstagioDocenciaBase(BaseModel):
    """Atributos comuns do estágio docência."""
    id_estudante: int = Field(..., description="ID do estudante")
    id_professor_supervisor: int = Field(..., description="ID do professor supervisor")
    id_disciplina: int = Field(..., description="ID da disciplina")
    id_semestre: int = Field(..., description="ID do semestre letivo")
    status_proposta: Optional[enumStatus.StatusPropostaEstagio] = Field(
        default=enumStatus.StatusPropostaEstagio.PENDENTE,
        description="Status da proposta de estágio"
    )
    data_entrega_proposta: Optional[date] = Field(
        default=None, 
        description="Data em que a proposta foi entregue"
    )
    status_relatorio: Optional[enumStatus.StatusRelatorioEstagio] = Field(
        default=enumStatus.StatusRelatorioEstagio.PENDENTE,
        description="Status do relatório de estágio"
    )
    data_entrega_relatorio: Optional[date] = Field(
        default=None, 
        description="Data em que o relatório foi entregue"
    )


class EstagioDocenciaCreate(EstagioDocenciaBase):
    """Schema para cadastro de um novo estágio docência (POST)."""
    pass


class EstagioDocenciaUpdate(BaseModel):
    """Schema para atualização parcial de dados do estágio (PATCH/PUT)."""
    id_estudante: Optional[int] = None
    id_professor_supervisor: Optional[int] = None
    id_disciplina: Optional[int] = None
    id_semestre: Optional[int] = None
    status_proposta: Optional[enumStatus.StatusPropostaEstagio] = None
    data_entrega_proposta: Optional[date] = None
    status_relatorio: Optional[enumStatus.StatusRelatorioEstagio] = None
    data_entrega_relatorio: Optional[date] = None


class EstagioDocenciaResponse(EstagioDocenciaBase):
    """Schema de resposta retornado pela API (contém a chave primária)."""
    id_estagio: int

    model_config = ConfigDict(from_attributes=True)

# ==========================================
# SCHEMAS DE PROFICIÊNCIA
# ==========================================

class ProficienciaBase(BaseModel):
    """Atributos comuns da proficiência."""
    id_proficiencia: int = Field(..., description="ID da proficiência")
    id_estudante: int = Field(..., description="ID do estudante")
    status_certificado: enumStatus.StatusCertificadoProficiencia = Field(..., max_length=20, description="Status do certificado")
    data_entrega_certificado: Optional[date] = Field(None, description="Data de entrega do certificado")
    consolidada_sigaa: bool = Field(..., description="Indica se a proficiência está consolidada no SIGAA")

class ProficienciaCreate(ProficienciaBase):
    """Schema para cadastro de uma nova proficiência (POST)."""
    pass

class ProficienciaUpdate(BaseModel):
    """Schema para atualização parcial de dados da proficiência (PATCH/PUT)."""
    id_proficiencia: Optional[int] = None
    id_estudante: Optional[int] = None
    status_certificado: Optional[enumStatus.StatusCertificadoProficiencia] = None
    data_entrega_certificado: Optional[date] = None
    consolidada_sigaa: Optional[bool] = None

class ProficienciaResponse(ProficienciaBase):
    """Schema de resposta retornado pela API (contém a chave primária)."""
    id_proficiencia: int

    model_config = ConfigDict(from_attributes=True)

# ==========================================
# SCHEMAS DE SUBMISSÕES DE ARTIGOS
# ==========================================

class SubmissaoArtigoBase(BaseModel):
    """Atributos base da submissão de artigo."""
    id_artigo : int = Field(..., description="ID do artigo")
    titulo : str = Field(..., max_length=270, description="Título do artigo")
    id_estudante : int = Field(..., description="ID do estudante")
    status_comprovante : enumStatus.StatusComprovanteArtigo = Field(..., description="Status do comprovante de submissão do artigo")
    data_entrega : Optional[date] = Field(None, description="Data de entrega do comprovante")
    qualis : Optional[str] = Field(None, max_length=2, description="Qualis do periódico ou conferência")
    tipo : enumStatus.TipoArtigo = Field(..., description="Tipo do artigo (ex: CONFERENCIA, PERIODICO, CAPITULO_LIVRO)")
    status_validacao_colegiado : enumStatus.StatusValidacaoColegiadoArtigo = Field(..., description="Status de validação do colegiado")

class SubmissaoArtigoCreate(SubmissaoArtigoBase):
    """Schema para cadastro de uma nova submissão de artigo (POST)."""
    pass

class SubmissaoArtigoUpdate(BaseModel):
    """Schema para atualização parcial de dados da submissão de artigo (PATCH/PUT)."""
    id_artigo: Optional[int] = None
    titulo: Optional[str] = Field(None, max_length=270)
    id_estudante: Optional[int] = None
    status_comprovante: Optional[enumStatus.StatusComprovanteArtigo] = None
    data_entrega: Optional[date] = None
    qualis: Optional[str] = Field(None, max_length=2)
    tipo: Optional[enumStatus.TipoArtigo] = None
    status_validacao_colegiado: Optional[enumStatus.StatusValidacaoColegiadoArtigo] = None

class SubmissaoArtigoResponse(SubmissaoArtigoBase):
    """Schema de resposta retornado pela API (contém a chave primária)."""
    id_submissao: int

    model_config = ConfigDict(from_attributes=True)

# ==========================================
# SCHEMAS DE HISTÓRICO DE DISCIPLINAS
# ==========================================

class HistoricoDisciplinaBase(BaseModel):
    """Atributos base do histórico de disciplina."""
    id_estudante: int = Field(..., description="ID do estudante")
    id_disciplina: int = Field(..., description="ID da disciplina")
    id_semestre: int = Field(..., description="ID do semestre letivo")
    conceito: Optional[enumStatus.ConceitoHistorico] = Field(
        default=None, 
        description="Conceito obtido pelo discente (A, B, C, D)"
    )
    status_disciplina: Optional[enumStatus.StatusDisciplina] = Field(
        default=enumStatus.StatusDisciplina.PENDENTE,
        description="Status do histórico na disciplina"
    )
    creditos_integralizados: Optional[int] = Field(
        default=0, 
        ge=0, 
        description="Quantidade de créditos obtidos após aprovação"
    )


class HistoricoDisciplinaCreate(HistoricoDisciplinaBase):
    """Schema para matrícula/registro inicial em uma disciplina (POST)."""
    pass


class HistoricoDisciplinaUpdate(BaseModel):
    """Schema para atualização de conceito, status ou créditos (PATCH/PUT)."""
    id_estudante: Optional[int] = None
    id_disciplina: Optional[int] = None
    id_semestre: Optional[int] = None
    conceito: Optional[enumStatus.ConceitoHistorico] = None
    status_disciplina: Optional[enumStatus.StatusDisciplina] = None
    creditos_integralizados: Optional[int] = Field(None, ge=0)


class HistoricoDisciplinaResponse(HistoricoDisciplinaBase):
    """Schema de resposta retornado pela API (contém a chave primária id_historico)."""
    id_historico: int

    model_config = ConfigDict(from_attributes=True)

# ==========================================
# SCHEMAS DE DISSERTAÇÃO
# ==========================================

class DissertacaoBase(BaseModel):
    """Atributos comuns da dissertação."""
    id_estudante: int = Field(..., description="ID do estudante")
    titulo: str = Field(..., max_length=255, description="Título da dissertação")
    data_inicio: Optional[date] = Field(None, description="Data de início da dissertação")
    status_dissertacao: enumStatus.StatusDissertacao = Field(
        default=enumStatus.StatusDissertacao.EM_ANDAMENTO,
        description="Status atual da dissertação"
    )

class DissertacaoCreate(DissertacaoBase):
    """Schema para cadastro de uma nova dissertação (POST)."""
    pass

class DissertacaoUpdate(BaseModel):
    """Schema para atualização parcial de dados da dissertação (PATCH/PUT)."""
    id_estudante: Optional[int] = None
    titulo: Optional[str] = Field(None, max_length=255)
    data_defesa: Optional[date] = None
    status_dissertacao: Optional[enumStatus.StatusDissertacao] = None

class DissertacaoResponse(DissertacaoBase):
    """Schema de resposta retornado pela API (contém a chave primária id_dissertacao)."""
    id_dissertacao: int

    model_config = ConfigDict(from_attributes=True)
    
# ==========================================
# SCHEMAS DE QUALIFICAÇÃO
# ==========================================

class QualificacaoBase(BaseModel):
    """Atributos comuns da qualificação."""
    id_dissertacao: int = Field(..., description="ID da dissertação")
    prazo_maximo_qualificacao: Optional[date] = Field(None, description="Prazo máximo para a qualificação")
    status_qualificacao: enumStatus.StatusQualificacao = Field(
        default=enumStatus.StatusQualificacao.PENDENTE,
        description="Status atual da qualificação"
    )
    retorno_qualificacao: Optional[str] = Field(None, description="Ato do discente após a qualificação (Solicitou Banca ou Solicitou Prorrogação.)")
    tentativa: Optional[int] = Field(None, description="Número de tentativas realizadas para a qualificação")
    data_realizacao: Optional[date] = Field(None, description="Data da qualificação")
    
class QualificacaoCreate(QualificacaoBase):
    """Schema para cadastro de uma nova qualificação (POST)."""
    pass    

class QualificacaoUpdate(BaseModel):
    """Schema para atualização parcial de dados da qualificação (PATCH/PUT)."""
    id_dissertacao: Optional[int] = None
    prazo_maximo_qualificacao: Optional[date] = None
    status_qualificacao: Optional[enumStatus.StatusQualificacao] = None
    retorno_qualificacao: Optional[str] = None
    tentativa: Optional[int] = None
    data_realizacao: Optional[date] = None

class QualificacaoResponse(QualificacaoBase):
    """Schema de resposta retornado pela API (contém a chave primária id_qualificacao)."""
    id_qualificacao: int

    model_config = ConfigDict(from_attributes=True)

# ==========================================
# SCHEMAS DE DEFESA
# ==========================================

class DefesaBase(BaseModel):
    """Atributos Comuns da Defesa"""
    
    # PK e FK
    id_defesa : int = Field(..., description="ID da defesa")
    id_dissertacao : int = Field(..., description="ID da dissertação")
    
    # --- Fase 1: Homologação da Banca
    prazo_solicitacao_homologacao_banca: Optional[date] = Field(None, description="Prazo para solicitação de homologação da banca")
    data_solicitacao_banca: Optional[date] = Field(None, description="Data de solicitação da banca")
    status_homologacao_banca: Optional[enumStatus.StatusHomologacaoBanca] = Field(
        default=enumStatus.StatusHomologacaoBanca.PENDENTE,
        description="Status da homologação da banca"
    )
    
    # --- Fase 2: Realização e Conceito da Defesa
    prazo_maximo_defesa: Optional[date] = Field(None, description="Prazo máximo para a defesa")
    data_realizacao: Optional[date] = Field(None, description="Data de realização da defesa")
    status_defesa: Optional[enumStatus.StatusDefesa] = Field(
        default=enumStatus.StatusDefesa.PENDENTE,
        description="Status da defesa")
    retorno_defesa: Optional[str] = Field(None, description="Ato do discente após a defesa (Solicitou Banca ou Solicitou Prorrogação.)")
    conceito_defesa: Optional[enumStatus.ConceitoDefesa] = Field(None, description="Conceito obtido na defesa (Aprovado, Aprovado Condicionalmente ou Reprovado)")
    prazo_versao_final: Optional[date] = Field(None, description="Prazo para entrega da versão final da dissertação")
    
    # --- Fase 3: Processo de Diploma
    prazo_limite_processo_diploma: Optional[date] = Field(None, description="Prazo máximo para o processo de diploma")
    status_processo_diploma: Optional[enumStatus.StatusProcessoDiploma] = Field(
        default=enumStatus.StatusProcessoDiploma.PENDENTE,
        description="Status do processo de diploma"
    )


# ===========================================
# SCHEMAS DE PRORROGAÇÃO 
# ===========================================

class ProrrogacaoBase(BaseModel):
    """Atributos comuns da prorrogação."""
    id_estudante: int = Field(..., description="ID do estudante")
    tipo_prazo : enumStatus.TipoPrazoProrrogacao = Field(
        ...,
        description="Tipo de prazo da prorrogação"
    )
    quantidade_meses: int = Field(..., gt=0, description="Quantidade de meses da prorrogação")
    data_pedido: date = Field(..., description="Data do pedido de prorrogação")
    resultado_pedido: Optional[enumStatus.ResultadoPedidoProrrogacao] = Field(
        default=None,
        description="Resultado do pedido de prorrogação"
    )

class ProrrogacaoCreate(ProrrogacaoBase):
    """Schema para cadastro de uma nova prorrogação (POST)."""
    pass

class ProrrogacaoUpdate(BaseModel):
    """Schema para atualização parcial de dados da prorrogação (PATCH/PUT)."""
    id_estudante: Optional[int] = None
    tipo_prazo: Optional[enumStatus.TipoPrazoProrrogacao] = None
    quantidade_meses: Optional[int] = Field(None, gt=0)
    data_pedido: Optional[date] = None
    resultado_pedido: Optional[enumStatus.ResultadoPedidoProrrogacao] = None

class ProrrogacaoResponse(ProrrogacaoBase):
    """Schema de resposta retornado pela API (contém a chave primária id_prorrogacao)."""
    id_prorrogacao: int

    model_config = ConfigDict(from_attributes=True)