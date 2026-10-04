from typing import List, Optional
from sqlalchemy.orm import Session
from db import models
from schemas import HistoricoDisciplinaCreate, HistoricoDisciplinaUpdate


def criar_historico_disciplina(
    db: Session, 
    historico_in: HistoricoDisciplinaCreate
) -> models.HistoricoDisciplina:
    """Registra uma nova disciplina no histórico do estudante."""
    db_historico = models.HistoricoDisciplina(**historico_in.model_dump())
    db.add(db_historico)
    db.commit()
    db.refresh(db_historico)
    return db_historico


def listar_historicos_disciplinas(
    db: Session, 
    skip: int = 0, 
    limit: int = 100
) -> List[models.HistoricoDisciplina]:
    """Retorna uma lista paginada de todos os registros de histórico."""
    return db.query(models.HistoricoDisciplina).offset(skip).limit(limit).all()


def buscar_historico_por_id(
    db: Session, 
    id_historico: int
) -> Optional[models.HistoricoDisciplina]:
    """Busca um registro de histórico pelo ID da chave primária."""
    return (
        db.query(models.HistoricoDisciplina)
        .filter(models.HistoricoDisciplina.id_historico == id_historico)
        .first()
    )


def buscar_historicos_por_estudante(
    db: Session, 
    id_estudante: int
) -> List[models.HistoricoDisciplina]:
    """Busca todo o histórico escolar de um estudante específico."""
    return (
        db.query(models.HistoricoDisciplina)
        .filter(models.HistoricoDisciplina.id_estudante == id_estudante)
        .all()
    )


def atualizar_historico_disciplina(
    db: Session, 
    id_historico: int, 
    atualizacoes: HistoricoDisciplinaUpdate
) -> Optional[models.HistoricoDisciplina]:
    """Atualiza o status, conceito ou créditos de um registro no histórico."""
    db_historico = buscar_historico_por_id(db, id_historico)
    if not db_historico:
        return None

    dados_atualizacao = atualizacoes.model_dump(exclude_unset=True)

    for chave, valor in dados_atualizacao.items():
        setattr(db_historico, chave, valor)

    db.commit()
    db.refresh(db_historico)
    return db_historico


def deletar_historico_disciplina(db: Session, id_historico: int) -> bool:
    """Remove um registro do histórico pelo ID."""
    db_historico = buscar_historico_por_id(db, id_historico)
    if not db_historico:
        return False

    db.delete(db_historico)
    db.commit()
    return True