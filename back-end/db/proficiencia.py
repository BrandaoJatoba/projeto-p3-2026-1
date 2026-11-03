from datetime import date
from sqlalchemy.orm import Session
from db import models
from typing import List, Optional, Dict, Any
from db.enumStatus import StatusCertificadoProficiencia

def cadastrar_proficiencia(
    db_connection: Session, 
    id_estudante: int,
    status_certificado: StatusCertificadoProficiencia,
    data_entrega_certificado: Optional[date] = None,
    consolidada_sigaa: bool = False
) -> models.Proficiencia:
    """Cadastra uma nova proficiência no sistema."""
    nova_proficiencia = models.Proficiencia(
        id_estudante = id_estudante,
        status_certificado = status_certificado,
        data_entrega_certificado = data_entrega_certificado,
        consolidada_sigaa = consolidada_sigaa
    )
    db_connection.add(nova_proficiencia)
    db_connection.commit()
    db_connection.refresh(nova_proficiencia)
    return nova_proficiencia

def listar_proficiencias(db_connection: Session, skip: int = 0, limit: int = 100) -> List[models.Proficiencia]:
    """Retorna uma lista paginada de todas as proficiências."""
    return db_connection.query(models.Proficiencia).offset(skip).limit(limit).all()

def buscar_proficiencia_por_id(
    db_connection: Session,
    id_proficiencia: int
) -> Optional[models.Proficiencia]:
    return (
        db_connection.query(models.Proficiencia)
        .filter(models.Proficiencia.id_proficiencia == id_proficiencia)
        .first()
    )

def atualizar_proficiencia(db_connection: Session, id_proficiencia: int, dados_atualizacao: Dict[str, Any]) -> Optional[models.Proficiencia]:
    """Atualiza campos específicos de uma proficiência existente."""
    proficiencia = buscar_proficiencia_por_id(db_connection, id_proficiencia)
    if not proficiencia:
        return None
        
    for chave, valor in dados_atualizacao.items():
        if hasattr(proficiencia, chave):
            setattr(proficiencia, chave, valor)

    db_connection.commit()
    db_connection.refresh(proficiencia)

    return proficiencia

def deletar_proficiencia(db_connection: Session, id_proficiencia: int) -> bool:
    """Deleta uma proficiência existente."""
    proficiencia = buscar_proficiencia_por_id(db_connection, id_proficiencia)
    if not proficiencia:
        return False
        
    db_connection.delete(proficiencia)
    db_connection.commit()
    return True
