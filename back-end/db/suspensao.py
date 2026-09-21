from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from datetime import date
from db import models

# ==========================================
# CRUD: SUSPENSÃO DE CALENDÁRIO
# ==========================================

def criar_suspensao_calendario(
    db_connection: Session, 
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
    db_connection.add(nova_suspensao)
    db_connection.commit()
    db_connection.refresh(nova_suspensao)
    return nova_suspensao

def buscar_suspensao(db_connection: Session, id_suspensao: int) -> Optional[models.SuspensaoCalendario]:
    """Retorna os dados de uma paralisação específica."""
    return db_connection.query(models.SuspensaoCalendario).filter(models.SuspensaoCalendario.id_suspensao == id_suspensao).first()

def listar_suspensoes_por_semestre(db_connection: Session, id_semestre: int) -> List[models.SuspensaoCalendario]:
    """Lista todas as suspensões vinculadas a um determinado semestre letivo."""
    return db_connection.query(models.SuspensaoCalendario).filter(models.SuspensaoCalendario.id_semestre == id_semestre).all()

def atualizar_suspensao(db_connection: Session, id_suspensao: int, dados_atualizacao: Dict[str, Any]) -> Optional[models.SuspensaoCalendario]:
    """Atualiza informações de uma suspensão (ex: adicionar data de fim)."""
    suspensao = buscar_suspensao(db_connection, id_suspensao)
    if not suspensao:
        return None
        
    for chave, valor in dados_atualizacao.items():
        if hasattr(suspensao, chave):
            setattr(suspensao, chave, valor)
            
    db_connection.commit()
    db_connection.refresh(suspensao)
    return suspensao

def deletar_suspensao(db_connection: Session, id_suspensao: int) -> bool:
    """Remove o registro de uma suspensão."""
    suspensao = buscar_suspensao(db_connection, id_suspensao)
    if suspensao:
        db_connection.delete(suspensao)
        db_connection.commit()
        return True
    return False


