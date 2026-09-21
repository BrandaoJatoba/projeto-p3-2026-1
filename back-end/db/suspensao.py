from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from datetime import date
from db import models

# ==========================================
# CRUD: SUSPENSÃO DE CALENDÁRIO
# ==========================================

def criar_suspensao_calendario(
    db: Session, 
    id_semestre: int, 
    data_inicio_suspensao: date, 
    motivo: Optional[str] = None, 
    data_fim_suspensao: Optional[date] = None, 
    dias_suspensos: Optional[int] = None
) -> models.SuspensaoCalendario:
    """Registra uma nova suspensão associada a um semestre letivo."""
    nova_suspensao = models.SuspensaoCalendario(
        id_semestre=id_semestre,
        motivo=motivo,
        data_inicio_suspensao=data_inicio_suspensao,
        data_fim_suspensao=data_fim_suspensao,
        dias_suspensos=dias_suspensos
    )
    db.add(nova_suspensao)
    db.commit()
    db.refresh(nova_suspensao)
    return nova_suspensao

def buscar_suspensao(db: Session, id_suspensao: int) -> Optional[models.SuspensaoCalendario]:
    """Retorna os dados de uma paralisação específica."""
    return db.query(models.SuspensaoCalendario).filter(models.SuspensaoCalendario.id_suspensao == id_suspensao).first()

def listar_todas_suspensoes(db: Session) -> List[models.SuspensaoCalendario]:
    """Retorna todas as suspensões cadastradas no sistema."""
    return db.query(models.SuspensaoCalendario).all()

def listar_suspensoes_por_semestre(db: Session, id_semestre: int) -> List[models.SuspensaoCalendario]:
    """Lista todas as suspensões vinculadas a um determinado semestre letivo."""
    return db.query(models.SuspensaoCalendario).filter(models.SuspensaoCalendario.id_semestre == id_semestre).all()

def atualizar_suspensao(db: Session, id_suspensao: int, dados_atualizacao: Dict[str, Any]) -> Optional[models.SuspensaoCalendario]:
    """Atualiza informações de uma suspensão (ex: adicionar data de fim)."""
    suspensao = buscar_suspensao(db, id_suspensao)
    if not suspensao:
        return None
        
    for chave, valor in dados_atualizacao.items():
        if hasattr(suspensao, chave):
            setattr(suspensao, chave, valor)
            
    db.commit()
    db.refresh(suspensao)
    return suspensao

def deletar_suspensao(db: Session, id_suspensao: int) -> bool:
    """Remove o registro de uma suspensão."""
    suspensao = buscar_suspensao(db, id_suspensao)
    if suspensao:
        db.delete(suspensao)
        db.commit()
        return True
    return False