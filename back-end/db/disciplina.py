from datetime import date
from sqlalchemy.orm import Session
from db import models
from typing import List, Optional, Dict, Any

def criar_disciplina(
    db_connection: Session, 
    codigo_disciplina: str, 
    nome_disciplina: str, 
    grupo_disciplina: str, 
    creditos: int
) -> models.Disciplina:
    """Cria um novo registro de disciplina."""
    nova_disciplina = models.Disciplina(
        nome=nome_disciplina,
        codigo=codigo_disciplina,
        grupo=grupo_disciplina,
        creditos=creditos
    )
    db_connection.add(nova_disciplina)
    db_connection.commit()
    db_connection.refresh(nova_disciplina)
    return nova_disciplina

def listar_disciplinas(db_connection: Session, skip: int = 0) -> List[models.Disciplina]:
    """Retorna uma lista paginada de todas as disciplinas."""
    return db_connection.query(models.Disciplina).offset(skip).all()

def buscar_disciplina_por_id(
    db_connection: Session,
    id_disciplina: int
):
    return (
        db_connection.query(models.Disciplina)
        .filter(models.Disciplina.id_disciplina == id_disciplina)
        .first()
    )

def atualizar_disciplina(db_connection: Session, id_disciplina: int, dados_atualizacao: Dict[str, Any]) -> Optional[models.Disciplina]:
    """Atualiza campos específicos de uma disciplina existente."""
    disciplina = buscar_disciplina_por_id(db_connection, id_disciplina)
    if not disciplina:
        return None
        
    for chave, valor in dados_atualizacao.items():
        if hasattr(disciplina, chave):
            setattr(disciplina, chave, valor)

    db_connection.commit()
    db_connection.refresh(disciplina)

    return disciplina

def buscar_disciplina_por_codigo(
    db_connection: Session,
    codigo: str
):
    return (
        db_connection.query(models.Disciplina)
        .filter(models.Disciplina.codigo_disciplina == codigo)
        .first()
    )  
    
def deletar_disciplina(db_connection: Session, id_disciplina: int) -> bool:
    """Deleta uma disciplina pelo seu ID."""
    disciplina = buscar_disciplina_por_id(db_connection, id_disciplina)
    if not disciplina:
        return False
    
    db_connection.delete(disciplina)
    db_connection.commit()
    return True
