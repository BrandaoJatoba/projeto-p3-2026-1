from datetime import date
from sqlalchemy.orm import Session
from db import models
from typing import List, Optional, Dict, Any

def criar_estudante(
    db_connection: Session,
    matricula: str,
    nome_discente: str,
    status_atual: str,
    id_semestre: int,
    id_orientador: Optional[int] = None,
    eh_bolsista: Optional[bool] = False,
    prazo_conclusao_sigaa: Optional[date] = None,
    email: Optional[str] = None
):
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
    for key, value in updates.items():
        setattr(estudante, key, value)
    db_connection.commit()
    db_connection.refresh(estudante)
    return estudante

def deletar_estudante(db_connection: Session, matricula: str) -> bool:
    estudante = buscar_estudante_por_matricula(db_connection, matricula)
    if not estudante:
        return False
    db_connection.delete(estudante)
    db_connection.commit()
    return True

def listar_estudantes(db_connection: Session) -> List[models.Estudante]:
    return db_connection.query(models.Estudante).all() 

def buscar_estudantes_por_orientador(db_connection: Session, id_orientador: int) -> List[models.Estudante]:
    return db_connection.query(models.Estudante).filter(models.Estudante.id_orientador == id_orientador).all()

def buscar_estudantes_por_semestre(db_connection: Session, id_semestre: int) -> List[models.Estudante]:
    return db_connection.query(models.Estudante).filter(models.Estudante.id_semestre == id_semestre).all()

def buscar_estudantes_por_status(db_connection: Session, status_atual: str) -> List[models.Estudante]:
    return db_connection.query(models.Estudante).filter(models.Estudante.status_atual == status_atual).all()

def buscar_estudantes_por_bolsa(db_connection: Session, eh_bolsista: bool) -> List[models.Estudante]:
    return db_connection.query(models.Estudante).filter(models.Estudante.eh_bolsista == eh_bolsista).all()

def buscar_estudantes_por_prazo_conclusao(db_connection: Session, prazo_conclusao_sigaa: date) -> List[models.Estudante]:
    return db_connection.query(models.Estudante).filter(models.Estudante.prazo_conclusao_sigaa <= prazo_conclusao_sigaa).all()
