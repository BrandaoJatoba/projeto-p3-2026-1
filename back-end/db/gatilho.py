from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.orm import Session

from db import models


# ==========================================
# CRUD - GatilhoAlerta
# ==========================================

def criar_gatilho_alerta(
    db_connection: Session, 
    id_tipo_prazo: int, 
    dias_antecedencia: int, 
    mensagem_template: Optional[str] = None,
    ativo: bool = True
) -> models.GatilhoAlerta:
    """Cria um novo GatilhoAlerta associado a um TipoPrazo."""
    novo_gatilho = models.GatilhoAlerta(
        id_tipo_prazo=id_tipo_prazo,
        dias_antecedencia=dias_antecedencia,
        mensagem_template=mensagem_template,
        ativo=ativo
    )
    db_connection.add(novo_gatilho)
    db_connection.commit()
    db_connection.refresh(novo_gatilho)
    return novo_gatilho


def obter_gatilho_alerta_por_id(
    db_connection: Session, 
    id_gatilho: int
) -> Optional[models.GatilhoAlerta]:
    """Busca um GatilhoAlerta pelo seu ID."""
    return db_connection.get(models.GatilhoAlerta, id_gatilho)


def listar_gatilhos_por_tipo_prazo(
    db_connection: Session, 
    id_tipo_prazo: int, 
    apenas_ativos: bool = False
) -> List[models.GatilhoAlerta]:
    """Lista todos os gatilhos vinculados a um TipoPrazo específico."""
    stmt = select(models.GatilhoAlerta).where(models.GatilhoAlerta.id_tipo_prazo == id_tipo_prazo)
    if apenas_ativos:
        stmt = stmt.where(models.GatilhoAlerta.ativo.is_(True))
    return list(db_connection.scalars(stmt).all())


def atualizar_gatilho_alerta(
    db_connection: Session, 
    id_gatilho: int, 
    dias_antecedencia: Optional[int] = None,
    mensagem_template: Optional[str] = None,
    ativo: Optional[bool] = None
) -> Optional[models.GatilhoAlerta]:
    """Atualiza um GatilhoAlerta existente."""
    gatilho = obter_gatilho_alerta_por_id(db_connection, id_gatilho)
    if not gatilho:
        return None
    
    if dias_antecedencia is not None:
        gatilho.dias_antecedencia = dias_antecedencia
    if mensagem_template is not None:
        gatilho.mensagem_template = mensagem_template
    if ativo is not None:
        gatilho.ativo = ativo

    db_connection.commit()
    db_connection.refresh(gatilho)
    return gatilho


def deletar_gatilho_alerta(db_connection: Session, id_gatilho: int) -> bool:
    """Remove um GatilhoAlerta pelo ID."""
    gatilho = obter_gatilho_alerta_por_id(db_connection, id_gatilho)
    if not gatilho:
        return False
    
    db_connection.delete(gatilho)
    db_connection.commit()
    return True