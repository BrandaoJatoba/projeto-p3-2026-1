"""
Motor de varredura de alertas (Alert Engine).

    Varre gatilhos ativos x estudantes elegíveis e devolve os alertas pendentes.
    Para cada aluno e tipo de prazo, considera só o gatilho mais próximo do prazo
    (menor dias_antecedencia com dias_restantes <= dias_antecedencia, inclui vencidos);
    se esse gatilho já tem registro ENVIADO no histórico, o prazo não aparece.
    
"""

from datetime import date
from typing import Optional

# Faixas de urgência (em dias restantes até o prazo)
LIMITE_CRITICO = 7
LIMITE_ATENCAO = 30


def classificar_urgencia(dias_restantes: int) -> str:
    """
    Classifica a urgência de um alerta:
    - CRITICO: 7 dias ou menos (inclui prazos já vencidos, com valor negativo)
    - ATENCAO: de 8 a 30 dias
    - PREVENTIVO: mais de 30 dias
    """
    if dias_restantes <= LIMITE_CRITICO:
        return "CRITICO"

    if dias_restantes <= LIMITE_ATENCAO:
        return "ATENCAO"

    return "PREVENTIVO"

def calcular_dias_restantes(data_limite: date, hoje: Optional[date] = None) -> int:
    """
    Retorna quantos dias faltam até data_limite.
    Valor negativo = prazo já vencido (ex.: -3 significa 'venceu há 3 dias').

    `hoje` é opcional para permitir testes com datas fixas;
    se não for informado, usa a data atual.
    """
    if hoje is None:
        hoje = date.today()

    return (data_limite - hoje).days

"""
Motor de varredura de alertas (Alert Engine).

Cruza os gatilhos ativos com as datas-limite acadêmicas dos discentes
e monta a lista de alertas pendentes para a Central de Alertas.

Só calcula e lista: não envia e-mail nem grava histórico (CLAUDE.md §12 e §20).

Decisões provisórias (aguardando confirmação do tech leader):
- As datas de qualificação e defesa já são gravadas com prorrogações e
  suspensões por `prazos_service.recalcular_prazos_estudante`; por isso o
  motor NÃO soma suspensões de novo (evita contagem dupla).
- HOMOLOGACAO_BANCA usa `Defesa.prazo_maximo_defesa` como data-base
  (os gatilhos padrão de 45/35 dias contam até a defesa).
- Prazos pós-defesa também consideram estudantes com status PÓS DEFESA.
"""

from datetime import date
from typing import Callable, Dict, List, Optional

from sqlalchemy.orm import Session

from db import alerta as crud_alerta
from db import models
from db.enumStatus import (
    StatusDefesa,
    StatusEstudanteEnum,
    StatusHomologacaoBanca,
    StatusProcessoDiploma,
    TipoOrientacao,
)
from services.prazos_service import STATUS_DEFESA_ENCERRADA, STATUS_QUALIFICACAO_ENCERRADA

# Faixas de urgência (em dias restantes até o prazo)
LIMITE_CRITICO = 7
LIMITE_ATENCAO = 30


def classificar_urgencia(dias_restantes: int) -> str:
    """
    Classifica a urgência de um alerta:
    - CRITICO: 7 dias ou menos (inclui prazos já vencidos, com valor negativo)
    - ATENCAO: de 8 a 30 dias
    - PREVENTIVO: mais de 30 dias
    """
    if dias_restantes <= LIMITE_CRITICO:
        return "CRITICO"

    if dias_restantes <= LIMITE_ATENCAO:
        return "ATENCAO"

    return "PREVENTIVO"


def calcular_dias_restantes(data_limite: date, hoje: Optional[date] = None) -> int:
    """
    Retorna quantos dias faltam até data_limite.
    Valor negativo = prazo já vencido (ex.: -3 significa 'venceu há 3 dias').

    `hoje` é opcional para permitir testes com datas fixas;
    se não for informado, usa a data atual.
    """
    if hoje is None:
        hoje = date.today()

    return (data_limite - hoje).days


# ==========================================================================
# EXTRATORES DE DATA-LIMITE (um por codigo_prazo)
# Cada um recebe (estudante, qualificacao, defesa) e devolve a data-limite
# ou None quando aquele prazo não se aplica ao aluno no momento.
# ==========================================================================

def _data_qualificacao(estudante, qualificacao, defesa) -> Optional[date]:
    if estudante.status_atual != StatusEstudanteEnum.ATIVO:
        return None
    if qualificacao is None or qualificacao.status_qualificacao in STATUS_QUALIFICACAO_ENCERRADA:
        return None
    return qualificacao.prazo_maximo_qualificacao


def _data_homologacao_banca(estudante, qualificacao, defesa) -> Optional[date]:
    if estudante.status_atual != StatusEstudanteEnum.ATIVO:
        return None
    if defesa is None or defesa.status_defesa in STATUS_DEFESA_ENCERRADA:
        return None
    if defesa.status_homologacao_banca != StatusHomologacaoBanca.PENDENTE.value:
        return None
    return defesa.prazo_maximo_defesa


def _data_defesa(estudante, qualificacao, defesa) -> Optional[date]:
    if estudante.status_atual != StatusEstudanteEnum.ATIVO:
        return None
    if defesa is None or defesa.status_defesa in STATUS_DEFESA_ENCERRADA:
        return None
    return defesa.prazo_maximo_defesa


def _data_versao_final(estudante, qualificacao, defesa) -> Optional[date]:
    if defesa is None or defesa.status_defesa != StatusDefesa.AGUARDANDO_VERSAO_FINAL.value:
        return None
    return defesa.prazo_versao_final


def _data_diploma(estudante, qualificacao, defesa) -> Optional[date]:
    if defesa is None or defesa.status_processo_diploma != StatusProcessoDiploma.PENDENTE.value:
        return None
    return defesa.prazo_limite_processo_diploma


def _data_conclusao_sigaa(estudante, qualificacao, defesa) -> Optional[date]:
    if estudante.status_atual != StatusEstudanteEnum.ATIVO:
        return None
    return estudante.prazo_conclusao_sigaa


EXTRATORES_DATA: Dict[str, Callable] = {
    "QUALIFICACAO": _data_qualificacao,
    "HOMOLOGACAO_BANCA": _data_homologacao_banca,
    "DEFESA": _data_defesa,
    "VERSAO_FINAL_DEFESA": _data_versao_final,
    "DIPLOMA_POS_DEFESA": _data_diploma,
    "CONCLUSAO_SIGAA": _data_conclusao_sigaa,
}


def _montar_orientadores(estudante: models.Estudante) -> List[dict]:
    """Lista de orientadores (principal primeiro), já carregada via selectinload."""
    vinculos = sorted(
        (v for v in estudante.orientacoes if v.professor is not None),
        key=lambda v: (
            0 if v.tipo_orientacao == TipoOrientacao.ORIENTADOR.value else 1,
            v.professor.nome_professor.lower(),
        ),
    )
    return [
        {
            "id_professor": v.professor.id_professor,
            "nome_professor": v.professor.nome_professor,
            "email": v.professor.email,
            "tipo_orientacao": v.tipo_orientacao,
        }
        for v in vinculos
    ]


# ==========================================================================
# MOTOR
# ==========================================================================

def listar_alertas_pendentes(db_connection: Session, hoje: Optional[date] = None) -> List[dict]:
    """
    Varre gatilhos ativos x estudantes elegíveis e devolve os alertas pendentes:
    entram os pares em que dias_restantes <= dias_antecedencia (inclui vencidos)
    e que ainda não têm registro ENVIADO no histórico.

    Ordenado do mais urgente (menos dias restantes) para o menos urgente.
    """
    if hoje is None:
        hoje = date.today()

    # 1. Consultas em lote (quantidade fixa de consultas, independe do nº de alunos)
    gatilhos = crud_alerta.listar_gatilhos_ativos_com_tipo(db_connection)
    if not gatilhos:
        return []

    # Do menor para o maior dias_antecedencia: o primeiro gatilho em que o aluno
    # se encaixa é o "mais próximo" do prazo (os maiores já ficaram para trás).
    gatilhos.sort(key=lambda par: par[0].dias_antecedencia)

    estudantes = crud_alerta.listar_estudantes_para_varredura(
        db_connection,
        [StatusEstudanteEnum.ATIVO, StatusEstudanteEnum.POS_DEFESA],
    )
    ids_estudantes = [e.id_estudante for e in estudantes]
    qualificacoes = crud_alerta.mapear_qualificacoes_atuais(db_connection, ids_estudantes)
    defesas = crud_alerta.mapear_defesas_atuais(db_connection, ids_estudantes)
    ja_enviados = crud_alerta.obter_pares_alertas_enviados(db_connection)

    # 2. Cruzamento em memória
    pendentes: List[dict] = []
    for estudante in estudantes:
        qualificacao = qualificacoes.get(estudante.id_estudante)
        defesa = defesas.get(estudante.id_estudante)
        orientadores = None  # montado só se o aluno tiver algum alerta
        prazos_resolvidos: set[int] = set()  # id_tipo_prazo já decididos p/ este aluno

        for gatilho, tipo_prazo in gatilhos:
            if tipo_prazo.id_tipo_prazo in prazos_resolvidos:
                continue  # já achamos o gatilho mais próximo deste prazo

            extrator = EXTRATORES_DATA.get(tipo_prazo.codigo_prazo)
            if extrator is None:
                continue  # tipo de prazo sem regra de data conhecida

            data_limite = extrator(estudante, qualificacao, defesa)
            if data_limite is None:
                continue

            dias_restantes = calcular_dias_restantes(data_limite, hoje)
            if dias_restantes > gatilho.dias_antecedencia:
                continue

            # Este é o gatilho mais próximo: os de antecedência maior são ignorados,
            # mesmo que nunca tenham sido enviados (evita "faltam 6 meses" com 4 dias).
            prazos_resolvidos.add(tipo_prazo.id_tipo_prazo)

            if (estudante.id_estudante, gatilho.id_gatilho) in ja_enviados:
                continue

            if orientadores is None:
                orientadores = _montar_orientadores(estudante)

            pendentes.append(
                {
                    "id_estudante": estudante.id_estudante,
                    "nome_discente": estudante.nome_discente,
                    "matricula": estudante.matricula,
                    "email": estudante.email,
                    "eh_bolsista": bool(estudante.eh_bolsista),
                    "id_gatilho": gatilho.id_gatilho,
                    "dias_antecedencia": gatilho.dias_antecedencia,
                    "id_tipo_prazo": tipo_prazo.id_tipo_prazo,
                    "codigo_prazo": tipo_prazo.codigo_prazo,
                    "nome_prazo": tipo_prazo.nome_prazo,
                    "data_limite": data_limite,
                    "dias_restantes": dias_restantes,
                    "urgencia": classificar_urgencia(dias_restantes),
                    "orientadores": orientadores,
                    "orientador_sem_email": any(not o["email"] for o in orientadores),
                }
            )

    pendentes.sort(key=lambda a: (a["dias_restantes"], a["nome_discente"].lower()))
    return pendentes

