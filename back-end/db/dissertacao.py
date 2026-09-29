from sqlalchemy.orm import Session
from db import models
from typing import List, Optional, Dict, Any
from schemas import DissertacaoCreate, DissertacaoUpdate

def criar_dissertacao(db: Session, dissertacao: DissertacaoCreate) -> models.Dissertacao:
    db.add(dissertacao)
    db.commit()
    db.refresh(dissertacao)
    return dissertacao

def obter_dissertacao_por_id(db: Session, dissertacao_id: int) -> Optional[models.Dissertacao]:
    return db.query(models.Dissertacao).filter(models.Dissertacao.id == dissertacao_id).first()

def atualizar_dissertacao(db: Session, dissertacao_id: int, dissertacao_update: DissertacaoUpdate) -> Optional[models.Dissertacao]:
    dissertacao = db.query(models.Dissertacao).filter(models.Dissertacao.id == dissertacao_id).first()
    
    if not dissertacao:
        return None
    
    for key, value in dissertacao_update.model_dump(exclude_unset=True).items():
        setattr(dissertacao, key, value)
    
    db.commit()
    db.refresh(dissertacao)
    return dissertacao

def deletar_dissertacao(db: Session, dissertacao_id: int) -> bool:
    dissertacao = db.query(models.Dissertacao).filter(models.Dissertacao.id == dissertacao_id).first()
    if dissertacao:
        db.delete(dissertacao)
        db.commit()
        return True
    return False

def listar_dissertacoes(db: Session, skip: int = 0, limit: int = 100) -> List[models.Dissertacao]:
    return db.query(models.Dissertacao).offset(skip).limit(limit).all()

def buscar_dissertacoes(db: Session, filtros: Dict[str, Any]) -> List[models.Dissertacao]:
    query = db.query(models.Dissertacao)
    for key, value in filtros.items():
        if hasattr(models.Dissertacao, key):
            query = query.filter(getattr(models.Dissertacao, key) == value)
    return query.all() 
