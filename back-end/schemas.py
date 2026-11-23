from datetime import date, datetime
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator, computed_field
from typing import Optional, List
import db.enumStatus as enumStatus

class SemestreCriacao(BaseModel):
    codigo_semestre: str = Field(max_length=6)
    data_inicio_real: date
    data_fim_real: date
    dias_letivos: int
    data_quinzena_override: Optional[date] = None

class SemestreAtualizacao(BaseModel):
    data_inicio_real: date
    data_fim_real: date
    dias_letivos: int
    data_quinzena_override: Optional[date] = None

class SemestreResposta(BaseModel):

    model_config = ConfigDict(from_attributes=True)

    id_semestre: int
    codigo_semestre: str
    data_inicio_real: Optional[date]
    data_fim_real: Optional[date]
    dias_letivos: Optional[int]
    data_quinzena_override: Optional[date] = None

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
    dias_antecedencia: int = Field(..., ge=0, example=30)
    mensagem_template: Optional[str] = Field(None, example="Atenção: Faltam {dias} dias para a sua qualificação.")
    ativo: bool = Field(default=True)

class GatilhoAlertaCreate(GatilhoAlertaBase):
    pass

class GatilhoAlertaUpdate(BaseModel):
    dias_antecedencia: Optional[int] = Field(None, ge=0)
    mensagem_template: Optional[str] = None
    ativo: Optional[bool] = None

class GatilhoAlertaResponse(GatilhoAlertaBase):
    id_gatilho: int

    model_config = ConfigDict(from_attributes=True)

class HistoricoAlertaEnviadoCreate(BaseModel):
    id_estudante: int = Field(..., gt=0)
    id_gatilho: int = Field(..., gt=0)
    destinatario_email: Optional[EmailStr] = None
    emails_cc: Optional[str] = None
    status_envio: enumStatus.StatusEnvioAlerta = Field(
        default=enumStatus.StatusEnvioAlerta.ENVIADO
    )

# ==================
# SCHEMAS DE HISTÓRICO DE ALERTAS ENVIADOS
# =================

class HistoricoAlertaEnviadoUpdate(BaseModel):
    destinatario_email: Optional[EmailStr] = None
    emails_cc: Optional[str] = None
    status_envio: Optional[enumStatus.StatusEnvioAlerta] = None
    data_envio: Optional[datetime] = None


class HistoricoAlertaEnviadoResponse(BaseModel):
    id_historico_alerta: int
    id_estudante: int
    id_gatilho: int
    data_envio: datetime
    destinatario_email: str
    emails_cc: Optional[str] = None
    status_envio: enumStatus.StatusEnvioAlerta
    assunto: Optional[str] = None
    corpo_mensagem: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class HistoricoAlertaPaginado(BaseModel):
    total: int
    skip: int
    limit: int
    itens: List[HistoricoAlertaEnviadoResponse]


class HistoricoAlertaDetalhado(HistoricoAlertaEnviadoResponse):
    """Registro do histórico enriquecido para a tela de auditoria."""
    nome_discente: str
    matricula: str
    nome_prazo: str


class HistoricoAlertaDetalhadoPaginado(BaseModel):
    total: int
    skip: int
    limit: int
    itens: List[HistoricoAlertaDetalhado]


# ==========================================
# SCHEMAS DE DISPARO DE ALERTAS
# ==========================================

class AjusteCcDisparo(BaseModel):
    """Ajustes opcionais da Secretaria nos destinatários em cópia (CC)."""
    cc_adicionais: Optional[List[EmailStr]] = Field(
        None, description="E-mails extras em cópia, além dos orientadores."
    )
    ignorar_cc_ids: Optional[List[int]] = Field(
        None,
        description="id_professor dos orientadores/coorientadores que NÃO vão em cópia.",
    )


class DisparoIndividualRequest(AjusteCcDisparo):
    id_estudante: int = Field(..., gt=0)
    id_gatilho: int = Field(..., gt=0)
    assunto: str = Field(..., min_length=1, max_length=255)
    corpo_mensagem: str = Field(..., min_length=1)
    email_destino: Optional[EmailStr] = Field(
        None, description="Sobrescreve o e-mail do discente (padrão: Estudante.email)."
    )


class ItemDisparoLote(AjusteCcDisparo):
    id_estudante: int = Field(..., gt=0)
    id_gatilho: int = Field(..., gt=0)
    assunto: Optional[str] = Field(None, max_length=255)
    corpo_mensagem: Optional[str] = None


class DisparoLoteRequest(BaseModel):
    itens: List[ItemDisparoLote] = Field(..., min_length=1)
    template_global_override: Optional[str] = Field(
        None,
        description=(
            "Texto usado no lugar do template do gatilho para os itens que não "
            "trazem assunto/corpo próprios."
        ),
    )


class ItemDisparoRecusado(BaseModel):
    id_estudante: int
    id_gatilho: int
    motivo: str


class DisparoLoteResponse(BaseModel):
    status: str = "PROCESSANDO"
    itens_aceitos: int
    recusados: List[ItemDisparoRecusado]


# ==========================================
# SCHEMAS DO MOTOR DE ALERTAS (PENDENTES)
# ==========================================

class OrientadorAlerta(BaseModel):
    id_professor: int
    nome_professor: str
    email: Optional[str] = None
    tipo_orientacao: str


class AlertaPendenteResponse(BaseModel):
    id_estudante: int
    nome_discente: str
    matricula: str
    email: str
    eh_bolsista: bool
    id_gatilho: int
    dias_antecedencia: int
    id_tipo_prazo: int
    codigo_prazo: str
    nome_prazo: str
    data_limite: date
    dias_restantes: int
    urgencia: str  # CRITICO | ATENCAO | PREVENTIVO
    orientadores: List[OrientadorAlerta]
    orientador_sem_email: bool

# ==========================================
# SCHEMAS DE MINUTAS DE E-MAIL
# ==========================================

class MinutaItemRequest(BaseModel):
    """Um alerta pendente selecionado na tela (par aluno + gatilho)."""
    id_estudante: int = Field(..., gt=0)
    id_gatilho: int = Field(..., gt=0)


class MinutaPreviewRequest(BaseModel):
    itens: List[MinutaItemRequest] = Field(..., min_length=1)
    template_customizado: Optional[str] = Field(
        None,
        description="Texto para testar no lugar do template do gatilho (vale para todos os itens).",
    )


class MinutaResponse(BaseModel):
    id_estudante: int
    id_gatilho: int
    nome_discente: str
    destinatario: Optional[str] = None
    cc: List[str]
    assunto: str
    corpo: str
    avisos: List[str]
    destinatarios_cc: List[OrientadorAlerta] = []
    corpo_html: str

class MinutaIgnorada(BaseModel):
    id_estudante: int
    id_gatilho: int
    motivo: str


class MinutaPreviewResponse(BaseModel):
    minutas: List[MinutaResponse]
    ignorados: List[MinutaIgnorada]
    
# ==========================================
# SCHEMAS DE DISCIPLINA
# ==========================================

class DisciplinaBase(BaseModel):
    """Atributos comuns partilhados entre schemas de disciplina."""
    codigo_disciplina: str = Field(
        ..., 
        max_length=20, 
        description="Código identificador da disciplina (ex: PPGI 001)",
        examples=["PPGI 001"]
    )
    nome_disciplina: str = Field(
        ..., 
        max_length=150,  # Aumentado para corresponder ao modelo da Base de Dados
        description="Nome da disciplina",
        examples=["Teoria da Computação"]
    )
    grupo_disciplina: enumStatus.GrupoPesquisa = Field(
        ..., 
        description="Grupo de pesquisa ao qual a disciplina pertence (ex: GRUPO 1)"
    )
    natureza_disciplina: enumStatus.NaturezaDisciplina = Field(
        ...,
        description="Natureza da disciplina (ex: BASICAS, ELETIVAS, TOPICOS_ESPECIAIS)"
    )
    creditos: int = Field(
        ..., 
        gt=0, 
        description="Quantidade de créditos (deve ser maior que zero)",
        examples=[4]
    )
    eh_obrigatoria: bool = Field(
        default=False,
        description="Indica se a disciplina é obrigatória"
    )

class DisciplinaCreate(DisciplinaBase):
    """Schema para criação de disciplina (dados enviados no corpo do POST)."""
    pass

class DisciplinaUpdate(BaseModel):
    """Schema para atualização parcial de disciplina (dados do PATCH/PUT)."""
    codigo_disciplina: Optional[str] = Field(None, max_length=20)
    nome_disciplina: Optional[str] = Field(None, max_length=150)
    grupo_disciplina: Optional[enumStatus.GrupoPesquisa] = None
    natureza_disciplina: Optional[enumStatus.NaturezaDisciplina] = None
    creditos: Optional[int] = Field(None, gt=0)
    eh_obrigatoria: Optional[bool] = None

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
    id_estudante: int = Field(..., description="ID do estudante")
    status_certificado: enumStatus.StatusCertificadoProficiencia = Field(..., description="Status do certificado")
    data_entrega_certificado: Optional[date] = Field(None, description="Data de entrega do certificado")
    consolidada_sigaa: bool = Field(default=False, description="Indica se a proficiência está consolidada no SIGAA")

class ProficienciaCreate(ProficienciaBase):
    """Schema para cadastro de uma nova proficiência (POST)."""
    pass

class ProficienciaUpdate(BaseModel):
    """Schema para atualização parcial de dados da proficiência (PATCH/PUT)."""
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
    titulo : str = Field(..., max_length=270, description="Título do artigo")
    id_estudante : int = Field(..., description="ID do estudante")
    status_comprovante : enumStatus.StatusComprovanteArtigo = Field(..., description="Status do comprovante de submissão do artigo")
    data_entrega : Optional[date] = Field(None, description="Data de entrega do comprovante")
    qualis : Optional[enumStatus.QualisArtigo] = Field(None, description="Qualis do periódico ou conferência")
    tipo : enumStatus.TipoArtigo = Field(..., description="Tipo do artigo (ex: CONFERENCIA, PERIODICO, CAPITULO_LIVRO)")
    status_validacao_colegiado : enumStatus.StatusValidacaoColegiadoArtigo = Field(..., description="Status de validação do colegiado")

class SubmissaoArtigoCreate(SubmissaoArtigoBase):
    """Schema para cadastro de uma nova submissão de artigo (POST)."""
    pass

class SubmissaoArtigoUpdate(BaseModel):
    """Schema para atualização parcial de dados da submissão de artigo (PATCH/PUT)."""
    titulo: Optional[str] = Field(None, max_length=270)
    id_estudante: Optional[int] = None
    status_comprovante: Optional[enumStatus.StatusComprovanteArtigo] = None
    data_entrega: Optional[date] = None
    qualis: Optional[enumStatus.QualisArtigo] = Field(None, description="Qualis do periódico ou conferência")
    tipo: Optional[enumStatus.TipoArtigo] = None
    status_validacao_colegiado: Optional[enumStatus.StatusValidacaoColegiadoArtigo] = None

class SubmissaoArtigoResponse(SubmissaoArtigoBase):
    """Schema de resposta retornado pela API (contém a chave primária)."""
    id_artigo: int

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
    titulo: Optional[str] = Field(None, max_length=255, description="Título da dissertação")
    data_inicio: date = Field(..., description="Data de início da dissertação")


class DissertacaoCreate(DissertacaoBase):
    """Schema para cadastro de uma nova dissertação (POST)."""
    pass

class DissertacaoUpdate(BaseModel):
    """Schema para atualização parcial de dados da dissertação (PATCH/PUT)."""
    id_estudante: Optional[int] = None
    titulo: Optional[str] = Field(None, max_length=255)
    data_inicio : Optional[date] = None

class DissertacaoResponse(DissertacaoBase):
    """Schema de resposta retornado pela API (contém a chave primária id_dissertacao)."""
    id_dissertacao: int
    
    model_config = ConfigDict(from_attributes=True)

    @field_validator('titulo', mode='before')
    @classmethod
    def substituir_titulo_nulo(cls, v):
        return v if v is not None else "A definir"
    
# ==========================================
# SCHEMAS DE QUALIFICAÇÃO
# ==========================================

class QualificacaoBase(BaseModel):
    """Atributos comuns da qualificação."""
    id_dissertacao: int = Field(..., description="ID da dissertação")
    prazo_maximo_qualificacao: date = Field(..., description="Prazo máximo para a qualificação")
    status_qualificacao: enumStatus.StatusQualificacao = Field(
        default=enumStatus.StatusQualificacao.PENDENTE,
        description="Status atual da qualificação"
    )
    tentativa: int = Field(default=1, description="Número de tentativas realizadas para a qualificação")
    data_realizacao: Optional[date] = Field(None, description="Data da qualificação")
    
class QualificacaoCreate(QualificacaoBase):
    """Schema para cadastro de uma nova qualificação (POST)."""
    pass    

class QualificacaoUpdate(BaseModel):
    """Schema para atualização parcial de dados da qualificação (PATCH/PUT)."""
    id_dissertacao: Optional[int] = None
    prazo_maximo_qualificacao: Optional[date] = None
    status_qualificacao: Optional[enumStatus.StatusQualificacao] = None
    tentativa: Optional[int] = None
    data_realizacao: Optional[date] = None

class QualificacaoResponse(QualificacaoBase):
    """Schema de resposta retornado pela API (contém a chave primária id_qualificacao)."""
    id_qualificacao: int

    model_config = ConfigDict(from_attributes=True)

# ==========================================
# SCHEMAS DE DEFESA
# ==========================================

def _validar_intervalo_homologacao_defesa(
    data_solicitacao: Optional[date],
    data_realizacao: Optional[date],
) -> None:
    if data_solicitacao and data_realizacao:
        if data_realizacao < data_solicitacao:
            raise ValueError(
                "A data de realização da defesa não pode ser anterior à data de solicitação da banca."
            )
        if (data_realizacao - data_solicitacao).days > 30:
            raise ValueError(
                "Conforme o Art. 37, VI do Regimento, a defesa deve ocorrer no máximo 30 dias após a solicitação de homologação da banca."
            )


class DefesaBase(BaseModel):
    """Atributos Comuns da Defesa"""
    
    # PK e FK
    id_dissertacao: int = Field(..., description="ID da dissertação")
    
    # --- Fase 1: Homologação da Banca ---
    data_solicitacao_banca: Optional[date] = Field(None, description="Data de solicitação da banca")
    status_homologacao_banca: Optional[enumStatus.StatusHomologacaoBanca] = Field(
        default=enumStatus.StatusHomologacaoBanca.PENDENTE,
        description="Status da homologação da banca"
    )
    
    # --- Fase 2: Realização e Conceito da Defesa ---
    prazo_maximo_defesa: date = Field(..., description="Prazo máximo para a defesa")
    data_realizacao: Optional[date] = Field(None, description="Data de realização da defesa")
    status_defesa: Optional[enumStatus.StatusDefesa] = Field(
        default=enumStatus.StatusDefesa.PENDENTE,
        description="Status da defesa"
    )
    conceito_defesa: Optional[enumStatus.ConceitoDefesa] = Field(
        None, 
        description="Conceito obtido na defesa (Aprovado, Aprovado Condicionalmente ou Reprovado)"
    )
    prazo_versao_final: Optional[date] = Field(None, description="Prazo para entrega da versão final da dissertação")
    
    # --- Fase 3: Processo de Diploma ---
    prazo_limite_processo_diploma: Optional[date] = Field(None, description="Prazo máximo para o processo de diploma")
    status_processo_diploma: Optional[enumStatus.StatusProcessoDiploma] = Field(
        default=enumStatus.StatusProcessoDiploma.PENDENTE,
        description="Status do processo de diploma"
    )


class DefesaCreate(DefesaBase):
    """Schema para cadastro de uma nova defesa (POST)."""

    @model_validator(mode="after")
    def validar_datas_banca(self):
        _validar_intervalo_homologacao_defesa(
            self.data_solicitacao_banca, 
            self.data_realizacao
        )
        return self


class DefesaUpdate(BaseModel):
    """Schema para atualização parcial de dados da defesa (PATCH/PUT)."""
    id_dissertacao: Optional[int] = None
    data_solicitacao_banca: Optional[date] = None
    status_homologacao_banca: Optional[enumStatus.StatusHomologacaoBanca] = None
    prazo_maximo_defesa: Optional[date] = None
    data_realizacao: Optional[date] = None
    status_defesa: Optional[enumStatus.StatusDefesa] = None
    conceito_defesa: Optional[enumStatus.ConceitoDefesa] = None
    prazo_versao_final: Optional[date] = None
    prazo_limite_processo_diploma: Optional[date] = None
    status_processo_diploma: Optional[enumStatus.StatusProcessoDiploma] = None

    @model_validator(mode="after")
    def validar_datas_banca(self):
        _validar_intervalo_homologacao_defesa(
            self.data_solicitacao_banca, 
            self.data_realizacao
        )
        return self


class DefesaResponse(DefesaBase):
    """Schema de resposta retornado pela API (contém a chave primária id_defesa)."""
    id_defesa: int

    model_config = ConfigDict(from_attributes=True)

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

# ==========================================
# Schemas para Orientação (N:N)
# ==========================================

class ProfessorResumo(BaseModel):
    id_professor: int
    nome_professor: str
    email: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class EstudanteOrientadorBase(BaseModel):
    id_professor: int = Field(..., gt=0)
    tipo_orientacao: enumStatus.TipoOrientacao = Field(
        default=enumStatus.TipoOrientacao.ORIENTADOR
    )


class EstudanteOrientadorCreate(EstudanteOrientadorBase):
    pass


class EstudanteOrientadorUpdate(BaseModel):
    tipo_orientacao: enumStatus.TipoOrientacao


class EstudanteOrientadorResponse(EstudanteOrientadorBase):
    id_estudante: int
    professor: Optional[ProfessorResumo] = None

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# Schemas para Estudante
# ==========================================

class EstudanteBase(BaseModel):
    matricula: str = Field(..., min_length=1, max_length=20)
    nome_discente: str = Field(..., min_length=1, max_length=100)
    status_atual: enumStatus.StatusEstudanteEnum = Field(
        default=enumStatus.StatusEstudanteEnum.ATIVO
    )
    id_semestre: int = Field(..., gt=0)
    eh_bolsista: bool = False
    prazo_conclusao_sigaa: Optional[date] = None
    email: Optional[EmailStr] = None


class EstudanteCreate(EstudanteBase):
    id_orientador: Optional[int] = Field(None, gt=0)
    orientacoes: Optional[List[EstudanteOrientadorCreate]] = None


class EstudanteUpdate(BaseModel):
    matricula: Optional[str] = Field(None, min_length=1, max_length=20)
    nome_discente: Optional[str] = Field(None, min_length=1, max_length=100)
    status_atual: Optional[enumStatus.StatusEstudanteEnum] = None
    id_semestre: Optional[int] = Field(None, gt=0)
    eh_bolsista: Optional[bool] = None
    prazo_conclusao_sigaa: Optional[date] = None
    email: Optional[EmailStr] = None
    id_orientador: Optional[int] = None
    orientacoes: Optional[List[EstudanteOrientadorCreate]] = None


class EstudanteResponse(BaseModel):
    id_estudante: int
    matricula: str
    nome_discente: str
    status_atual: enumStatus.StatusEstudanteEnum
    id_semestre: int
    eh_bolsista: bool
    prazo_conclusao_sigaa: Optional[date] = None
    email: Optional[str] = None
    orientacoes: List[EstudanteOrientadorResponse] = []

    @computed_field
    @property
    def id_orientador(self) -> Optional[int]:
        for vinculo in self.orientacoes:
            if vinculo.tipo_orientacao == enumStatus.TipoOrientacao.ORIENTADOR:
                return vinculo.id_professor
        return None

    model_config = ConfigDict(from_attributes=True)


class EstudanteDetalhado(EstudanteResponse):
    dissertacao: Optional[DissertacaoResponse] = None
    qualificacao: Optional[QualificacaoResponse] = None
    defesa: Optional[DefesaResponse] = None


class EstudantePaginado(BaseModel):
    total: int
    skip: int
    limit: int
    itens: List[EstudanteResponse]


# Aliases de compatibilidade caso algum módulo ainda importe os nomes anteriores
EstudanteCriacao = EstudanteCreate
EstudanteAtualizacao = EstudanteUpdate
EstudanteResposta = EstudanteResponse


# ==========================
# SCHEMA DE PROFESSOR
# ==========================
class ProfessorCriacao(BaseModel):
    nome_professor: str = Field(..., min_length=2, max_length=100)
    email: Optional[EmailStr] = None

class ProfessorAtualizacao(BaseModel):
    nome_professor: Optional[str] = Field(None, min_length=2, max_length=100)
    email: Optional[EmailStr] = None

class ProfessorResposta(BaseModel):
    id_professor: int
    nome_professor: str
    email: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class ProfessorDetalhado(ProfessorResposta):
    """Perfil completo do professor, incluindo os estudantes orientados."""
    estudantes_orientados: list[EstudanteResponse] = []

# ===================================================
# Endpoint Apto para defesa
# ==================================================

class DetalheCreditos(BaseModel):
    total_valido: int
    basicas: int
    eletivas: int
    topicos_especiais: int
    estudo_dirigido: int
    requisito_obrigatorias_cumprido: bool

class RequisitosDefesa(BaseModel):
    creditos: bool
    proficiencia: bool
    estagio_docencia: bool
    qualificacao: bool
    artigo: bool

class StatusDefesaResponse(BaseModel):
    id_estudante: int
    apto_para_defesa: bool
    detalhe_creditos: DetalheCreditos
    requisitos: RequisitosDefesa
    pendencias_detalhadas: List[str]
