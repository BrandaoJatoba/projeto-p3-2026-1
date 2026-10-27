from typing import List, Optional
from sqlalchemy.orm import Session
from db import models
from schemas import ProrrogacaoCreate, ProrrogacaoUpdate


def criar_prorrogacao(
    db: Session, 
    prorrogacao: ProrrogacaoCreate
) -> models.Prorrogacao:
    """Cria um novo registro de pedido de prorrogação."""
    db_prorrogacao = models.Prorrogacao(**prorrogacao.model_dump())
    db.add(db_prorrogacao)
    db.commit()
    db.refresh(db_prorrogacao)
    return db_prorrogacao


def obter_prorrogacoes(
    db: Session, 
    skip: int = 0, 
    limit: int = 100
) -> List[models.Prorrogacao]:
    """Retorna a lista paginada de todas as prorrogações."""
    return db.query(models.Prorrogacao).offset(skip).limit(limit).all()


def obter_prorrogacao_por_id(
    db: Session, 
    id_prorrogacao: int
) -> Optional[models.Prorrogacao]:
    """Busca um registro de prorrogação pelo ID da chave primária."""
    return (
        db.query(models.Prorrogacao)
        .filter(models.Prorrogacao.id_prorrogacao == id_prorrogacao)
        .first()
    )


def obter_prorrogacoes_por_estudante(
    db: Session, 
    id_estudante: int
) -> List[models.Prorrogacao]:
    """Busca todas as prorrogações associadas a um estudante específico."""
    return (
        db.query(models.Prorrogacao)
        .filter(models.Prorrogacao.id_estudante == id_estudante)
        .all()
    )


def atualizar_prorrogacao(
    db: Session, 
    id_prorrogacao: int, 
    atualizacoes: ProrrogacaoUpdate
) -> Optional[models.Prorrogacao]:
    """Atualiza dinamicamente os campos fornecidos de uma prorrogação."""
    prorrogacao = obter_prorrogacao_por_id(db, id_prorrogacao)
    if not prorrogacao:
        return None

    dados_atualizacao = atualizacoes.model_dump(exclude_unset=True)
    for chave, valor in dados_atualizacao.items():
        setattr(prorrogacao, chave, valor)

    db.commit()
    db.refresh(prorrogacao)
    return prorrogacao


def deletar_prorrogacao(db: Session, id_prorrogacao: int) -> bool:
    """Deleta um registro de prorrogação do banco de dados pelo ID."""
    prorrogacao = obter_prorrogacao_por_id(db, id_prorrogacao)
    if not prorrogacao:
        return False

    db.delete(prorrogacao)
    db.commit()
    return True