from sqlalchemy.orm import Session
from db import models
from typing import List, Optional, Dict, Any
from datetime import date

def criar_defesa(db: Session, 
                 id_dissertacao: int,
                 prazo_solicitacao_homologacao_banca: int,
                 data_solicitacao_banca: Optional[date] = None,
                 status_solicitacao_banca: Optional[str] = None,
                 status_homologacao_banca: Optional[str] = None,
                 prazo_maximo_defesa: Optional[int] = None,
                 data_realizacao: Optional[date] = None,
                 status_defesa: Optional[str] = None,
                 retorno_defesa: Optional[str] = None,
                 conceito_defesa: Optional[str] = None,
                 prazo_versao_final: Optional[date] = None,
                 prazo_limite_processo_diploma: Optional[date] = None,
                 status_processo_diploma: Optional[str] = None,
                 ) -> models.Defesa:
    nova_defesa = models.Defesa(
        id_dissertacao=id_dissertacao,
        prazo_solicitacao_homologacao_banca=prazo_solicitacao_homologacao_banca,
        data_solicitacao_banca=data_solicitacao_banca,
        status_solicitacao_banca=status_solicitacao_banca,
        status_homologacao_banca=status_homologacao_banca,
        prazo_maximo_defesa=prazo_maximo_defesa,
        data_realizacao=data_realizacao,
        status_defesa=status_defesa,
        retorno_defesa=retorno_defesa,
        conceito_defesa=conceito_defesa,
        prazo_versao_final=prazo_versao_final,
        prazo_limite_processo_diploma=prazo_limite_processo_diploma,
        status_processo_diploma=status_processo_diploma
    )
    db.add(nova_defesa)
    db.commit()
    db.refresh(nova_defesa)
    return nova_defesa

def obter_defesa_por_id(db: Session, id_defesa: int) -> Optional[models.Defesa]:
    return db.query(models.Defesa).filter(models.Defesa.id_defesa == id_defesa).first()

def atualizar_defesa(db: Session, id_defesa: int, atualizacoes: Dict[str, Any]) -> Optional[models.Defesa]:
    defesa = obter_defesa_por_id(db, id_defesa)
    if defesa:
        for chave, valor in atualizacoes.items():
            setattr(defesa, chave, valor)
        db.commit()
        db.refresh(defesa)
    return defesa

def deletar_defesa(db: Session, id_defesa: int) -> bool:
    defesa = obter_defesa_por_id(db, id_defesa)
    if defesa:
        db.delete(defesa)
        db.commit()
        return True
    return False

def listar_defesas(db: Session) -> List[models.Defesa]:
    return db.query(models.Defesa).all()

def obter_defesa_por_dissertacao(db: Session, id_dissertacao: int) -> Optional[models.Defesa]:
    return db.query(models.Defesa).filter(models.Defesa.id_dissertacao == id_dissertacao).first()

def listar_defesas_por_status(db: Session, status_defesa: str) -> List[models.Defesa]:
    return db.query(models.Defesa).filter(models.Defesa.status_defesa == status_defesa).all()

def listar_defesas_por_filtro(db: Session, filtro: Dict[str, Any]) -> List[models.Defesa]:
    query = db.query(models.Defesa)
    for chave, valor in filtro.items():
        query = query.filter(getattr(models.Defesa, chave) == valor)
    return query.all()