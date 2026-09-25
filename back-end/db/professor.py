from sqlalchemy.orm import Session
from db import models
from typing import List, Optional, Dict, Any

def criar_professor(
    db_connection: Session, 
    nome_professor: str
) -> models.Professor:
    """Cria um novo registro de professor."""
    novo_professor = models.Professor(
        nome=nome_professor
        )
    db_connection.add(novo_professor)
    db_connection.commit()
    db_connection.refresh(novo_professor)
    return novo_professor

def listar_professores(db_connection: Session, skip: int = 0) -> List[models.Professor]:
    """Retorna uma lista paginada de todos os professores."""
    return db_connection.query(models.Professor).offset(skip).all()

def buscar_professor_por_id(
    db_connection: Session,
    id_professor: int
):
    return (
        db_connection.query(models.Professor)
        .filter(models.Professor.id_professor == id_professor)
        .first()
    )
    
def atualizar_professor(db_connection: Session, id_professor: int, dados_atualizacao: Dict[str, Any]) -> Optional[models.Professor]:
    """Atualiza campos específicos de um professor existente."""
    professor = buscar_professor_por_id(db_connection, id_professor)
    if not professor:
        return None
        
    for chave, valor in dados_atualizacao.items():
        if hasattr(professor, chave):
            setattr(professor, chave, valor)

    db_connection.commit()
    db_connection.refresh(professor)

    return professor
    
def deletar_professor(db_connection: Session, id_professor: int) -> bool:
    """Deleta um professor pelo seu ID."""
    professor = buscar_professor_por_id(db_connection, id_professor)
    if not professor:
        return False

    db_connection.delete(professor)
    db_connection.commit()
    return True

