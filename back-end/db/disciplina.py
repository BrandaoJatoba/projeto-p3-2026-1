from sqlalchemy.orm import Session
from db import models
from typing import List, Optional, Dict, Any

def criar_disciplina(
    db_connection: Session, 
    codigo_disciplina: str, 
    nome_disciplina: str, 
    grupo_pesquisa: str,          # Substitui o antigo grupo_disciplina
    natureza_disciplina: str,     # Novo campo
    creditos: int,
    eh_obrigatoria: bool = False  # Novo campo com valor por omissão
) -> models.Disciplina:
    """Cria um novo registo de disciplina."""
    nova_disciplina = models.Disciplina(
        nome_disciplina=nome_disciplina,
        codigo_disciplina=codigo_disciplina,
        grupo_pesquisa=grupo_pesquisa,               # Atualizado
        natureza_disciplina=natureza_disciplina,     # Atualizado
        creditos=creditos,
        eh_obrigatoria=eh_obrigatoria                # Atualizado
    )
    db_connection.add(nova_disciplina)
    db_connection.commit()
    db_connection.refresh(nova_disciplina)
    return nova_disciplina

def listar_disciplinas(db_connection: Session, skip: int = 0, limit: int = 100) -> List[models.Disciplina]:
    """Retorna uma lista paginada de todas as disciplinas."""
    return db_connection.query(models.Disciplina).offset(skip).limit(limit).all()

def buscar_disciplina_por_id(
    db_connection: Session,
    id_disciplina: int
 ) -> Optional[models.Disciplina]:
    return (
        db_connection.query(models.Disciplina)
        .filter(models.Disciplina.id_disciplina == id_disciplina)
        .first()
    )

def atualizar_disciplina(db_connection: Session, id_disciplina: int, dados_atualizacao: Dict[str, Any]) -> Optional[models.Disciplina]:
    """Atualiza campos especificos de uma disciplina existente."""
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
    codigo_disciplina: str
) -> Optional[models.Disciplina]:
    return (
        db_connection.query(models.Disciplina)
        .filter(models.Disciplina.codigo_disciplina == codigo_disciplina)
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
