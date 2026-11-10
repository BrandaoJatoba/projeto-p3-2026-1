from datetime import date
from dateutil.relativedelta import relativedelta
from sqlalchemy.orm import Session
from sqlalchemy import func

from db.models import (
    Estudante, 
    Dissertacao, 
    Qualificacao, 
    Defesa, 
    SuspensaoCalendario, 
    ProrrogacaoHistorico
)
import db.enumStatus as enumStatus
from services.academic_tracking_service import (
    MESES_PARA_QUALIFICACAO,
    MESES_PARA_DEFESA,
    somar_meses,
)

STATUS_QUALIFICACAO_ENCERRADA = {
    enumStatus.StatusQualificacao.DISPENSA.value,
    enumStatus.StatusQualificacao.REPROVADO_DEFINITIVO.value,
}

STATUS_DEFESA_ENCERRADA = {
    enumStatus.StatusDefesa.DEFENDIDA.value,
    enumStatus.StatusDefesa.CONCLUIDO.value,
    enumStatus.StatusDefesa.AGUARDANDO_VERSAO_FINAL.value,
    enumStatus.StatusDefesa.CANCELADO.value,
}

def _calcular_dias_suspensao_aplicaveis(
    suspensoes: list[SuspensaoCalendario],
    data_inicio_aluno: date,
    data_base_prazo: date,
) -> int:
    dias_totais = 0
    for s in suspensoes:
        if not s.dias_suspensos:
            continue

        fim = s.data_fim_suspensao or s.data_inicio_suspensao

        # O aluno já tinha começado antes da suspensão terminar
        # e o prazo ainda não tinha vencido quando ela começou
        if data_inicio_aluno <= fim and data_base_prazo >= s.data_inicio_suspensao:
            dias_totais += s.dias_suspensos

    return dias_totais


def recalcular_prazos_estudante(db: Session, id_estudante: int):
    """
    Recalcula do zero as datas limites de Qualificação e Defesa do estudante
    com base na data de início da dissertação, prorrogações aprovadas e suspensões.
    """
    
    # 1. Buscar os dados base do estudante
    estudante = db.query(Estudante).filter(Estudante.id_estudante == id_estudante).first()
    dissertacao = db.query(Dissertacao).filter(Dissertacao.id_estudante == id_estudante).first()
    
    if not estudante or not dissertacao or not dissertacao.data_inicio:
        return # Sem data base, não há o que calcular

    STATUS_RECALCULAVEIS = {
        enumStatus.StatusEstudanteEnum.ATIVO,
    }

    if estudante.status_atual not in STATUS_RECALCULAVEIS:
        return
    
    data_inicio = dissertacao.data_inicio

    # 2. Buscar todas as prorrogações aprovadas do estudante
    prorrogacoes = db.query(ProrrogacaoHistorico).filter(
        ProrrogacaoHistorico.id_estudante == id_estudante,
        ProrrogacaoHistorico.resultado_pedido == enumStatus.ResultadoPedidoProrrogacao.DEFERIDO.value
    ).all()

    meses_prorrogacao_qualificacao = sum(p.quantidade_meses for p in prorrogacoes if p.tipo_prazo == enumStatus.TipoPrazoProrrogacao.QUALIFICACAO.value)
    meses_prorrogacao_defesa = sum(p.quantidade_meses for p in prorrogacoes if p.tipo_prazo == enumStatus.TipoPrazoProrrogacao.DEFESA.value)

    # 3. Buscar suspensões ativas (com dias_suspensos já calculados)
    suspensoes = db.query(SuspensaoCalendario).filter(
        SuspensaoCalendario.dias_suspensos.isnot(None)
    ).all()

    # --- CÁLCULO DA QUALIFICAÇÃO ---
    qualificacao = (
    db.query(Qualificacao)
    .filter(Qualificacao.id_dissertacao == dissertacao.id_dissertacao)
    .order_by(Qualificacao.tentativa.desc(), Qualificacao.id_qualificacao.desc())
    .first()
)
    if qualificacao and qualificacao.status_qualificacao not in STATUS_QUALIFICACAO_ENCERRADA:
        data_base_qualificacao = somar_meses(
            data_inicio, MESES_PARA_QUALIFICACAO + meses_prorrogacao_qualificacao
        )
        dias_add = _calcular_dias_suspensao_aplicaveis(suspensoes, data_inicio, data_base_qualificacao)
        qualificacao.prazo_maximo_qualificacao = data_base_qualificacao + relativedelta(days=dias_add)

    # --- CÁLCULO DA DEFESA ---
# --- CÁLCULO DA DEFESA ---
    defesa = (
        db.query(Defesa)
        .filter(Defesa.id_dissertacao == dissertacao.id_dissertacao)
        .order_by(Defesa.id_defesa.desc())
        .first()
    )
    if defesa and defesa.status_defesa not in STATUS_DEFESA_ENCERRADA:
        data_base_defesa = somar_meses(
            data_inicio, MESES_PARA_DEFESA + meses_prorrogacao_defesa
        )
        dias_add = _calcular_dias_suspensao_aplicaveis(suspensoes, data_inicio, data_base_defesa)
        novo_prazo_defesa = data_base_defesa + relativedelta(days=dias_add)

        defesa.prazo_maximo_defesa = novo_prazo_defesa

        if estudante.prazo_conclusao_sigaa is None:
            estudante.prazo_conclusao_sigaa = novo_prazo_defesa

    db.commit()


def aplicar_suspensao_global(db: Session):
    """
    Gatilho para recalcular os prazos de TODOS os estudantes ativos.
    Deve ser chamado na rota do CRUD de Suspensão assim que a suspensão é finalizada/atualizada.
    """
    estudantes_ativos = db.query(Estudante.id_estudante).filter(
        Estudante.status_atual == enumStatus.StatusEstudanteEnum.ATIVO.value
    ).all()

    for (id_estudante,) in estudantes_ativos:
        recalcular_prazos_estudante(db, id_estudante)


def aplicar_prorrogacao_individual(db: Session, id_estudante: int):
    """
    Gatilho para atualizar a data de apenas um aluno.
    Deve ser chamado na rota de Prorrogação após o Colegiado aprovar o pedido.
    """
    recalcular_prazos_estudante(db, id_estudante)