from sqlalchemy.orm import Session
from db import models
from typing import List, Optional, Dict, Any
from datetime import date

def criar_qualificacao(
    db_connection: Session,
    id_dissertacao: int,
    prazo_maximo_qualificacao: date,
    status_qualificacao: str,
    retorno_qualificacao: Optional[str] = None,
    tentativa: int = 1,
    data_realizacao: Optional[date] = None,
) -> models.Qualificacao:
    """Cria um novo registro de qualificação."""
    nova_qualificacao = models.Qualificacao(
        id_dissertacao=id_dissertacao,
        prazo_maximo_qualificacao=prazo_maximo_qualificacao,
        status_qualificacao=status_qualificacao,
        retorno_qualificacao=retorno_qualificacao,
        tentativa=tentativa,
        data_realizacao=data_realizacao
    )
    
    db_connection.add(nova_qualificacao)
    db_connection.commit()
    db_connection.refresh(nova_qualificacao)
    return nova_qualificacao

def obter_qualificacao_por_id(db_connection: Session, id_qualificacao: int) -> Optional[models.Qualificacao]:
    """Obtém uma qualificação pelo seu ID."""
    return db_connection.query(models.Qualificacao).filter(models.Qualificacao.id_qualificacao == id_qualificacao).first()

def atualizar_qualificacao(
    db_connection: Session, 
    id_qualificacao: int, 
    atualizacoes: Dict[str, Any]
) -> Optional[models.Qualificacao]:
    """Atualiza uma qualificação existente."""
    qualificacao = obter_qualificacao_por_id(db_connection, id_qualificacao)
    if qualificacao:
        for chave, valor in atualizacoes.items():
            setattr(qualificacao, chave, valor)
        db_connection.commit()
        db_connection.refresh(qualificacao)
    return qualificacao

def deletar_qualificacao(db_connection: Session, id_qualificacao: int) -> bool:
    """Deleta uma qualificação pelo seu ID."""
    qualificacao = obter_qualificacao_por_id(db_connection, id_qualificacao)
    if qualificacao:
        db_connection.delete(qualificacao)
        db_connection.commit()
        return True
    return False

def listar_qualificacoes(db_connection: Session) -> List[models.Qualificacao]:
    """Lista todas as qualificações."""
    return db_connection.query(models.Qualificacao).all()

def listar_qualificacoes_por_status(db_connection: Session, status_qualificacao: str) -> List[models.Qualificacao]:
    """Lista todas as qualificações com um status específico."""
    return db_connection.query(models.Qualificacao).filter(models.Qualificacao.status_qualificacao == status_qualificacao).all()

def listar_qualificacoes_por_tentativa(db_connection: Session, tentativa: int) -> List[models.Qualificacao]:
    """Lista todas as qualificações com um número específico de tentativas."""
    return db_connection.query(models.Qualificacao).filter(models.Qualificacao.tentativa == tentativa).all()

def contar_qualificacoes_por_status(db_connection: Session, status_qualificacao: str) -> int:
    """Conta o número de qualificações com um status específico."""
    return db_connection.query(models.Qualificacao).filter(models.Qualificacao.status_qualificacao == status_qualificacao).count()

def contar_qualificacoes_por_tentativa(db_connection: Session, tentativa: int) -> int:
    """Conta o número de qualificações com um número específico de tentativas."""
    return db_connection.query(models.Qualificacao).filter(models.Qualificacao.tentativa == tentativa).count()

def obter_qualificacoes_por_filtro(
    db_connection: Session, 
    filtros: Dict[str, Any]
) -> List[models.Qualificacao]:
    """Obtém qualificações com base em filtros fornecidos."""
    query = db_connection.query(models.Qualificacao)
    for chave, valor in filtros.items():
        query = query.filter(getattr(models.Qualificacao, chave) == valor)
    return query.all()

def obter_qualificacao_por_data_realizacao(db_connection: Session, data_realizacao) -> List[models.Qualificacao]:
    """Obtém qualificações realizadas em uma data específica."""
    return db_connection.query(models.Qualificacao).filter(models.Qualificacao.data_realizacao == data_realizacao).all()
