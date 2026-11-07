from datetime import date
from typing import List, Optional, Dict, Any, Union, Tuple
from sqlalchemy import or_
from sqlalchemy.orm import Session
from db import models
# Importe o Enum do seu módulo de enums/models
from db.enumStatus import StatusEstudanteEnum, StatusQualificacao, StatusDefesa
from services.academic_tracking_service import AcademicTrackingService

from sqlalchemy import func, case
from db.models import Estudante, HistoricoDisciplina, Disciplina
from db.enumStatus import StatusDisciplina, ConceitoHistorico

def obter_resumo_creditos_por_perfil(db_connection: Session, id_estudante: int = None):
    """
    Agrupa os créditos integralizados por grupo de disciplina e identifica
    quantas vezes o discente obteve conceito 'D'.
    """
    
    # 1. Agregações condicionais (equivalente ao IF/CASE do SQL)
    soma_creditos = func.sum(
        case(
            (HistoricoDisciplina.status_disciplina == StatusDisciplina.APROVADO.value, HistoricoDisciplina.creditos_integralizados), 
            else_=0
        )
    ).label("total_creditos")
    
    # Conta quantas vezes o aluno tirou D nesse grupo de disciplinas
    qtd_conceito_d = func.sum(
        case(
            (HistoricoDisciplina.conceito == ConceitoHistorico.D.value, 1), 
            else_=0
        )
    ).label("qtd_conceito_d")

    # 2. Montagem da Query
    query = (
        db_connection.query(
            Estudante.id_estudante,
            Estudante.nome_discente,
            Disciplina.grupo_disciplina,
            soma_creditos,
            qtd_conceito_d
        )
        .join(HistoricoDisciplina, Estudante.id_estudante == HistoricoDisciplina.id_estudante)
        .join(Disciplina, HistoricoDisciplina.id_disciplina == Disciplina.id_disciplina)
        .group_by(
            Estudante.id_estudante,
            Estudante.nome_discente,
            Disciplina.grupo_disciplina
        )
    )

    # Filtro opcional para buscar de um aluno específico
    if id_estudante:
        query = query.filter(Estudante.id_estudante == id_estudante)

    return query.all()

# ==========================================================================
# CRIAÇÃO COM MARCOS (Eager Creation) — usada pelo POST /estudantes
# ==========================================================================

def criar_estudante_com_marcos(
    db_connection: Session,
    matricula: str,
    nome_discente: str,
    semestre: models.SemestreLetivo,
    id_orientador: Optional[int] = None,  # Adicione o parâmetro aqui
    eh_bolsista: bool = False,
    prazo_conclusao_sigaa: Optional[date] = None, # <--- 1. Adicione o parâmetro aqui
    email: Optional[str] = None,
) -> models.Estudante:
    """
    Cria, em UMA única transação, o estudante e seus registros de
    acompanhamento: DISSERTACOES, QUALIFICACOES e DEFESAS.
    """
    try:
        # 1. Estudante
        novo_estudante = models.Estudante(
            matricula=matricula,
            nome_discente=nome_discente,
            id_semestre=semestre.id_semestre,
            status_atual=StatusEstudanteEnum.ATIVO,
            eh_bolsista=eh_bolsista,
            id_orientador=id_orientador,  # Repasse a variável em vez de 'None'
            prazo_conclusao_sigaa=prazo_conclusao_sigaa,
            email=email,
        )
        db_connection.add(novo_estudante)
        db_connection.flush()  # gera novo_estudante.id_estudante sem confirmar

        # 2. Dissertação base, iniciando na data real de início do semestre
        nova_dissertacao = models.Dissertacao(
            id_estudante=novo_estudante.id_estudante,
            data_inicio=semestre.data_inicio_real,
        )
        db_connection.add(nova_dissertacao)
        db_connection.flush()  # gera nova_dissertacao.id_dissertacao

        # 3. Prazos regimentais (+18 e +24 meses)
        prazos = AcademicTrackingService.calcular_prazos_iniciais(semestre.data_inicio_real)

        # 4. Qualificação pendente
        db_connection.add(models.Qualificacao(
            id_dissertacao=nova_dissertacao.id_dissertacao,
            prazo_maximo_qualificacao=prazos.prazo_maximo_qualificacao,
            status_qualificacao=StatusQualificacao.PENDENTE.value,
            tentativa=1,
        ))

        # 5. Defesa pendente
        db_connection.add(models.Defesa(
            id_dissertacao=nova_dissertacao.id_dissertacao,
            prazo_maximo_defesa=prazos.prazo_maximo_defesa,
            status_defesa=StatusDefesa.PENDENTE.value,
        ))

        db_connection.commit()  # tudo ou nada
        db_connection.refresh(novo_estudante)
        return novo_estudante
    except Exception:
        db_connection.rollback()
        raise


def buscar_marcos_do_estudante(
    db_connection: Session,
    id_estudante: int,
) -> Tuple[Optional[models.Dissertacao], Optional[models.Qualificacao], Optional[models.Defesa]]:
    """
    Retorna (dissertacao, qualificacao, defesa) do estudante.
    Qualificação e defesa se ligam à DISSERTAÇÃO (id_dissertacao), não direto
    ao estudante, por isso primeiro buscamos a dissertação.

    Se houver mais de uma qualificação (2ª tentativa após reprovação),
    pegamos a mais recente (maior número de tentativa).
    """
    dissertacao = (
        db_connection.query(models.Dissertacao)
        .filter(models.Dissertacao.id_estudante == id_estudante)
        .first()
    )
    if dissertacao is None:
        return None, None, None

    qualificacao = (
        db_connection.query(models.Qualificacao)
        .filter(models.Qualificacao.id_dissertacao == dissertacao.id_dissertacao)
        .order_by(models.Qualificacao.tentativa.desc(), models.Qualificacao.id_qualificacao.desc())
        .first()
    )
    defesa = (
        db_connection.query(models.Defesa)
        .filter(models.Defesa.id_dissertacao == dissertacao.id_dissertacao)
        .order_by(models.Defesa.id_defesa.desc())
        .first()
    )
    return dissertacao, qualificacao, defesa


# ==========================================================================
# CONSULTAS
# ==========================================================================

def buscar_estudante_por_id(db_connection: Session, id_estudante: int) -> Optional[models.Estudante]:
    return (
        db_connection.query(models.Estudante)
        .filter(models.Estudante.id_estudante == id_estudante)
        .first()
    )


def buscar_estudante_por_matricula(db_connection: Session, matricula: str) -> Optional[models.Estudante]:
    return db_connection.query(models.Estudante).filter(models.Estudante.matricula == matricula).first()


def buscar_estudante_por_email(db_connection: Session, email: str) -> Optional[models.Estudante]:
    return db_connection.query(models.Estudante).filter(models.Estudante.email == email).first()


def listar_estudantes_filtrados(
    db_connection: Session,
    status_atual: Optional[StatusEstudanteEnum] = None,
    id_semestre: Optional[int] = None,
    id_orientador: Optional[int] = None,
    eh_bolsista: Optional[bool] = None,
    busca: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    ordenar_por: str = "nome_discente",
    ordem_desc: bool = False
) -> Tuple[int, List[models.Estudante]]:
    """
    Listagem paginada com filtros COMBINÁVEIS.

    O truque: a query do SQLAlchemy é "preguiçosa". Cada .filter() só acrescenta
    um AND ao WHERE; nada vai ao banco até chamarmos .count() ou .all().
    Então aplicamos cada filtro apenas SE ele foi enviado.

    Atenção ao `is not None`: com `if eh_bolsista:` o filtro eh_bolsista=False
    seria ignorado, porque False é "falsy" em Python.

    Retorna (total_sem_paginacao, itens_da_pagina).
    """
    query = db_connection.query(models.Estudante)

    if status_atual is not None:
        query = query.filter(models.Estudante.status_atual == status_atual)
    if id_semestre is not None:
        query = query.filter(models.Estudante.id_semestre == id_semestre)
    if id_orientador is not None:
        query = query.filter(models.Estudante.id_orientador == id_orientador)
    if eh_bolsista is not None:
        query = query.filter(models.Estudante.eh_bolsista == eh_bolsista)
    if busca:
        termo = f"%{busca.strip()}%"
        query = query.filter(
            or_(
                models.Estudante.nome_discente.ilike(termo),
                models.Estudante.matricula.ilike(termo),
            )
        )
        
    # Dicionário de segurança para garantir apenas colunas permitidas
    colunas_validas = {
        "nome_discente": models.Estudante.nome_discente,
        "matricula": models.Estudante.matricula,
        "status_atual": models.Estudante.status_atual
    }
    
    coluna = colunas_validas.get(ordenar_por, models.Estudante.nome_discente)

    if ordem_desc:
        query = query.order_by(coluna.desc())
    else:
        query = query.order_by(coluna.asc())
    total = query.count()  # conta ANTES de paginar
    itens = (
        query
        .offset(skip)
        .limit(limit)
        .all()
    )
    return total, itens


# ==========================================================================
# ATUALIZAÇÃO
# ==========================================================================

def atualizar_estudante_por_id(
    db_connection: Session,
    estudante: models.Estudante,
    updates: Dict[str, Any],
) -> models.Estudante:
    """
    Aplica apenas os campos enviados (vindo de model_dump(exclude_unset=True)).
    Recebe o objeto já buscado pela rota, que é quem decide o 404.
    """
    campos_protegidos = {"id_estudante", "matricula", "id_semestre"}

    try:
        for key, value in updates.items():
            if hasattr(estudante, key) and key not in campos_protegidos:
                setattr(estudante, key, value)
        db_connection.commit()
        db_connection.refresh(estudante)
        return estudante
    except Exception:
        db_connection.rollback()
        raise


# ==========================================================================
# FUNÇÕES QUE JÁ EXISTIAM NO REPOSITÓRIO (mantidas sem alteração)
# ==========================================================================

def criar_estudante(
    db_connection: Session,
    matricula: str,
    nome_discente: str,
    id_semestre: int,
    status_atual: StatusEstudanteEnum = StatusEstudanteEnum.ATIVO,
    id_orientador: Optional[int] = None,
    eh_bolsista: bool = False,
    prazo_conclusao_sigaa: Optional[date] = None,
    email: Optional[str] = None
) -> models.Estudante:
    try:
        novo_estudante = models.Estudante(
            matricula=matricula,
            nome_discente=nome_discente,
            status_atual=status_atual,
            id_semestre=id_semestre,
            id_orientador=id_orientador,
            eh_bolsista=eh_bolsista,
            prazo_conclusao_sigaa=prazo_conclusao_sigaa,
            email=email
        )
        db_connection.add(novo_estudante)
        db_connection.commit()
        db_connection.refresh(novo_estudante)
        return novo_estudante
    except Exception:
        db_connection.rollback()
        raise


def atualizar_estudante(
    db_connection: Session,
    matricula: str,
    updates: Dict[str, Any]
) -> Optional[models.Estudante]:
    estudante = buscar_estudante_por_matricula(db_connection, matricula)
    if not estudante:
        return None

    campos_protegidos = {"id_estudante"}

    try:
        for key, value in updates.items():
            if hasattr(estudante, key) and key not in campos_protegidos:
                setattr(estudante, key, value)
        db_connection.commit()
        db_connection.refresh(estudante)
        return estudante
    except Exception:
        db_connection.rollback()
        raise


def deletar_estudante(db_connection: Session, matricula: str) -> bool:
    # ATENÇÃO: nenhuma rota usa esta função. A regra de negócio proíbe deleção
    # física de estudantes (a saída do programa é feita via status_atual).
    # Sugestão: remover esta função para ninguém expô-la por engano.
    estudante = buscar_estudante_por_matricula(db_connection, matricula)
    if not estudante:
        return False
    try:
        db_connection.delete(estudante)
        db_connection.commit()
        return True
    except Exception:
        db_connection.rollback()
        raise


def listar_estudantes(db_connection: Session) -> List[models.Estudante]:
    return db_connection.query(models.Estudante).all()


def buscar_estudantes_por_orientador(db_connection: Session, id_orientador: int) -> List[models.Estudante]:
    return db_connection.query(models.Estudante).filter(models.Estudante.id_orientador == id_orientador).all()


def buscar_estudantes_por_semestre(db_connection: Session, id_semestre: int) -> List[models.Estudante]:
    return db_connection.query(models.Estudante).filter(models.Estudante.id_semestre == id_semestre).all()


def buscar_estudantes_por_status(
    db_connection: Session,
    status_atual: Union[StatusEstudanteEnum, str]
) -> List[models.Estudante]:
    return db_connection.query(models.Estudante).filter(models.Estudante.status_atual == status_atual).all()


def buscar_estudantes_por_bolsa(db_connection: Session, eh_bolsista: bool) -> List[models.Estudante]:
    return db_connection.query(models.Estudante).filter(models.Estudante.eh_bolsista == eh_bolsista).all()


def buscar_estudantes_por_prazo_conclusao(db_connection: Session, prazo_conclusao_sigaa: date) -> List[models.Estudante]:
    return db_connection.query(models.Estudante).filter(models.Estudante.prazo_conclusao_sigaa <= prazo_conclusao_sigaa).all()
