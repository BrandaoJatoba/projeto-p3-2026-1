from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.orm import Session

from db import models


# ==========================================
# CRUD - TipoPrazo
# ==========================================

def criar_tipo_prazo(
    db_connection: Session, 
    codigo_prazo: str, 
    nome_prazo: str, 
    descricao: Optional[str] = None
) -> models.TipoPrazo:
    """Cria um novo TipoPrazo."""
    novo_tipo_prazo = models.TipoPrazo(
        codigo_prazo=codigo_prazo,
        nome_prazo=nome_prazo,
        descricao=descricao
    )
    db_connection.add(novo_tipo_prazo)
    db_connection.commit()
    db_connection.refresh(novo_tipo_prazo)
    return novo_tipo_prazo


def obter_tipo_prazo_por_id(
    db_connection: Session, 
    id_tipo_prazo: int
) -> Optional[models.TipoPrazo]:
    """Busca um TipoPrazo pelo seu ID."""
    return db_connection.get(models.TipoPrazo, id_tipo_prazo)


def obter_tipo_prazo_por_codigo(
    db_connection: Session, 
    codigo_prazo: str
) -> Optional[models.TipoPrazo]:
    """Busca um TipoPrazo pelo código único."""
    stmt = select(models.TipoPrazo).where(models.TipoPrazo.codigo_prazo == codigo_prazo)
    return db_connection.scalar(stmt)


def listar_tipos_prazos(
    db_connection: Session, 
    pular: int = 0, 
    limite: int = 100
) -> List[models.TipoPrazo]:
    """Lista todos os tipos de prazos com paginação."""
    stmt = select(models.TipoPrazo).offset(pular).limit(limite)
    return list(db_connection.scalars(stmt).all())


def atualizar_tipo_prazo(
    db_connection: Session, 
    id_tipo_prazo: int, 
    codigo_prazo: Optional[str] = None,
    nome_prazo: Optional[str] = None,
    descricao: Optional[str] = None
) -> Optional[models.TipoPrazo]:
    """Atualiza dados de um TipoPrazo existente."""
    tipo_prazo = obter_tipo_prazo_por_id(db_connection, id_tipo_prazo)
    if not tipo_prazo:
        return None
    
    if codigo_prazo is not None:
        tipo_prazo.codigo_prazo = codigo_prazo
    if nome_prazo is not None:
        tipo_prazo.nome_prazo = nome_prazo
    if descricao is not None:
        tipo_prazo.descricao = descricao

    db_connection.commit()
    db_connection.refresh(tipo_prazo)
    return tipo_prazo


def deletar_tipo_prazo(db_connection: Session, id_tipo_prazo: int) -> bool:
    """Remove um TipoPrazo pelo ID."""
    tipo_prazo = obter_tipo_prazo_por_id(db_connection, id_tipo_prazo)
    if not tipo_prazo:
        return False
    
    db_connection.delete(tipo_prazo)
    db_connection.commit()
    return True