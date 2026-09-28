from datetime import date
from typing import List, Optional, Dict, Any, Union
from sqlalchemy.orm import Session
from db import models
# Importe o Enum do seu módulo de enums/models
from db.enumStatus import StatusEstudanteEnum 


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


def buscar_estudante_por_matricula(db_connection: Session, matricula: str) -> Optional[models.Estudante]:
    return db_connection.query(models.Estudante).filter(models.Estudante.matricula == matricula).first()


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