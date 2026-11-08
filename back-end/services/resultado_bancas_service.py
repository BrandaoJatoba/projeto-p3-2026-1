from datetime import date
from dateutil.relativedelta import relativedelta
from sqlalchemy.orm import Session
from sqlalchemy import func

from db.models import Estudante, Dissertacao, Qualificacao, Defesa
import db.enumStatus as enumStatus


def processar_resultado_qualificacao(db: Session, id_qualificacao: int, resultado: str, data_banca: date = None):
    """
    Processa a ata da banca de qualificação aplicando as regras do Regimento (Art. 23).
    """
    qualificacao = db.query(Qualificacao).filter(Qualificacao.id_qualificacao == id_qualificacao).first()
    if not qualificacao:
        return None

    dissertacao = db.query(Dissertacao).filter(Dissertacao.id_dissertacao == qualificacao.id_dissertacao).first()
    estudante = db.query(Estudante).filter(Estudante.id_estudante == dissertacao.id_estudante).first()

    data_base_calculo = data_banca or date.today()
    qualificacao.retorno_qualificacao = resultado
    qualificacao.data_realizacao = data_base_calculo

    if resultado == "APROVADO":
        qualificacao.status_qualificacao = "CONCLUIDO"
        
    elif resultado == "REPROVADO":
        if qualificacao.tentativa == 1:
            # Direito a uma repetição no prazo máximo de 3 meses[cite: 20]
            qualificacao.tentativa = 2
            qualificacao.status_qualificacao = "AGUARDANDO_NOVA_BANCA"
            qualificacao.prazo_maximo_qualificacao = data_base_calculo + relativedelta(months=3)
        else:
            # Segunda reprovação acarreta desligamento[cite: 20]
            qualificacao.status_qualificacao = "REPROVADO_DEFINITIVO"
            estudante.status_atual = enumStatus.StatusEstudanteEnum.DESLIGADO

    db.commit()
    db.refresh(qualificacao)
    return qualificacao


def processar_resultado_defesa(db: Session, id_defesa: int, conceito: str, data_banca: date = None):
    """
    Processa a ata da banca de defesa aplicando os prazos de 30 ou 60 dias (Art. 40).
    """
    defesa = db.query(Defesa).filter(Defesa.id_defesa == id_defesa).first()
    if not defesa:
        return None

    dissertacao = db.query(Dissertacao).filter(Dissertacao.id_dissertacao == defesa.id_dissertacao).first()
    estudante = db.query(Estudante).filter(Estudante.id_estudante == dissertacao.id_estudante).first()

    data_base_calculo = data_banca or date.today()
    defesa.conceito_defesa = conceito
    defesa.data_realizacao = data_base_calculo

    if conceito == "APROVADO":
        # Até 30 dias para alterações exigidas
        defesa.status_defesa = "AGUARDANDO_VERSAO_FINAL"
        defesa.prazo_versao_final = data_base_calculo + relativedelta(days=30)

    elif conceito == "APROVADO_CONDICIONALMENTE":
        # Até 60 dias para providenciar alterações
        defesa.status_defesa = "AGUARDANDO_VERSAO_FINAL"
        defesa.prazo_versao_final = data_base_calculo + relativedelta(days=60)

    elif conceito == "REPROVADO":
        # Desligamento imediato
        defesa.status_defesa = "REPROVADO_DEFINITIVO"
        defesa.prazo_versao_final = None
        estudante.status_atual = enumStatus.StatusEstudanteEnum.DESLIGADO

    db.commit()
    db.refresh(defesa)
    return defesa


def verificar_vencimento_entregas_finais(db: Session):
    """
    Rotina (cron job) para verificar alunos que estouraram o prazo de entrega da versão final.
    """
    defesas_vencidas = db.query(Defesa).filter(
        Defesa.status_defesa == "AGUARDANDO_VERSAO_FINAL",
        Defesa.prazo_versao_final < date.today()
    ).all()

    for defesa in defesas_vencidas:
        # Se não depositou a nova versão no prazo, é considerado reprovado e desligado
        defesa.conceito_defesa = "REPROVADO"
        defesa.status_defesa = "REPROVADO_POR_PRAZO"
        
        dissertacao = db.query(Dissertacao).filter(Dissertacao.id_dissertacao == defesa.id_dissertacao).first()
        if dissertacao:
            estudante = db.query(Estudante).filter(Estudante.id_estudante == dissertacao.id_estudante).first()
            if estudante:
                estudante.status_atual = enumStatus.StatusEstudanteEnum.DESLIGADO

    db.commit()
    return {"total_desligados": len(defesas_vencidas)}