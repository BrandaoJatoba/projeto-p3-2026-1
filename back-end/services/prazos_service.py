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

# Configurações Padrão do Programa (podem vir de variáveis de ambiente futuramente)
MESES_PADRAO_QUALIFICACAO = 12
MESES_PADRAO_DEFESA = 24


def _calcular_dias_suspensao_aplicaveis(
    suspensoes: list[SuspensaoCalendario], 
    data_base_prazo: date
) -> int:
    """
    Calcula os dias totais de suspensão a serem adicionados ao prazo.
    Atualmente afeta TODOS os prazos indistintamente, mas a arquitetura
    permite filtrar no futuro.
    """
    dias_totais = 0
    for suspensao in suspensoes:
        if not suspensao.dias_suspensos:
            continue
            
        # =====================================================================
        # TODO (Evolução Futura): 
        # Para que a greve afete apenas quem tinha prazo ativo durante ela,
        # substitua o "True" abaixo por uma lógica de interseção de datas.
        # Exemplo: if data_base_prazo >= suspensao.data_inicio_suspensao:
        # =====================================================================
        if True:
            dias_totais += suspensao.dias_suspensos
            
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

    data_inicio = dissertacao.data_inicio

    # 2. Buscar todas as prorrogações aprovadas do estudante
    prorrogacoes = db.query(ProrrogacaoHistorico).filter(
        ProrrogacaoHistorico.id_estudante == id_estudante,
        ProrrogacaoHistorico.resultado_pedido == enumStatus.ResultadoPedidoProrrogacao.APROVADO.value
    ).all()

    meses_prorrogacao_qualificacao = sum(p.quantidade_meses for p in prorrogacoes if p.tipo_prazo == enumStatus.TipoPrazoProrrogacao.QUALIFICACAO.value)
    meses_prorrogacao_defesa = sum(p.quantidade_meses for p in prorrogacoes if p.tipo_prazo == enumStatus.TipoPrazoProrrogacao.DEFESA.value)

    # 3. Buscar suspensões ativas (com dias_suspensos já calculados)
    suspensoes = db.query(SuspensaoCalendario).filter(
        SuspensaoCalendario.dias_suspensos.isnot(None)
    ).all()

    # --- CÁLCULO DA QUALIFICAÇÃO ---
    qualificacao = db.query(Qualificacao).filter(Qualificacao.id_dissertacao == dissertacao.id_dissertacao).first()
    if qualificacao:
        # Data Base (Início + Meses Padrão + Meses de Prorrogação)
        data_base_qualificacao = data_inicio + relativedelta(months=MESES_PADRAO_QUALIFICACAO + meses_prorrogacao_qualificacao)
        
        # Soma Dias de Suspensão
        dias_add = _calcular_dias_suspensao_aplicaveis(suspensoes, data_base_qualificacao)
        novo_prazo_qualificacao = data_base_qualificacao + relativedelta(days=dias_add)
        
        qualificacao.prazo_maximo_qualificacao = novo_prazo_qualificacao

    # --- CÁLCULO DA DEFESA ---
    defesa = db.query(Defesa).filter(Defesa.id_dissertacao == dissertacao.id_dissertacao).first()
    if defesa:
        # Data Base (Início + Meses Padrão + Meses Prorrogação Defesa)
        # Nota: Prorrogações de defesa podem acumular as de qualificação dependendo da regra do PPG. 
        # Aqui, isolamos cada tipo.
        data_base_defesa = data_inicio + relativedelta(months=MESES_PADRAO_DEFESA + meses_prorrogacao_defesa)
        
        # Soma Dias de Suspensão
        dias_add = _calcular_dias_suspensao_aplicaveis(suspensoes, data_base_defesa)
        novo_prazo_defesa = data_base_defesa + relativedelta(days=dias_add)
        
        defesa.prazo_maximo_defesa = novo_prazo_defesa
        
        # O prazo limite no SIGAA é amarrado à Defesa
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