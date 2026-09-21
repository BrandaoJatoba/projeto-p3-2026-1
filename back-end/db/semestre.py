from datetime import date
from sqlalchemy.orm import Session
import models
from typing import List, Optional, Dict, Any



def criar_semestre(
    db_connection: Session, 
    codigo_semestre: str, 
    data_inicio_real: Optional[date] = None, 
    data_fim_real: Optional[date] = None, 
    dias_letivos: Optional[int] = None
) -> models.SemestreLetivo:
    """Cria um novo registro de semestre letivo."""
    novo_semestre = models.SemestreLetivo(
        codigo_semestre=codigo_semestre,
        data_inicio_real=data_inicio_real,
        data_fim_real=data_fim_real,
        dias_letivos=dias_letivos
    )
    db_connection.add(novo_semestre)
    db_connection.commit()
    db_connection.refresh(novo_semestre)
    return novo_semestre

def listar_semestres_letivos(db_connection: Session, skip: int = 0) -> List[models.SemestreLetivo]:
    """Retorna uma lista paginada de todos os semestres letivos."""
    return db_connection.query(models.SemestreLetivo).offset(skip).all()

def buscar_semestre_por_id(
    db_connection: Session,
    id_semestre: int
):
    return (
        db_connection.query(models.SemestreLetivo)
        .filter(models.SemestreLetivo.id_semestre == id_semestre)
        .first()
    )

def atualizar_semestre_letivo(db_connection: Session, id_semestre: int, dados_atualizacao: Dict[str, Any]) -> Optional[models.SemestreLetivo]:
    """Atualiza campos específicos de um semestre letivo existente."""
    semestre = buscar_semestre_por_id(db_connection, id_semestre)
    if not semestre:
        return None
        
    for chave, valor in dados_atualizacao.items():
        if hasattr(semestre, chave):
            setattr(semestre, chave, valor)

    db_connection.commit()
    db_connection.refresh(semestre)

    return semestre

def buscar_semestre_por_codigo(
    db_connection: Session,
    codigo_semestre: str
):
    return (
        db_connection.query(models.SemestreLetivo)
        .filter(models.SemestreLetivo.codigo_semestre == codigo_semestre)
        .first()
    )
    
def deletar_semestre_letivo(db_connection: Session, id_semestre: int) -> bool:
    """Remove um semestre letivo pelo ID."""
    semestre = buscar_semestre_por_id(db_connection, id_semestre)
    if semestre:
        db_connection.delete(semestre)
        db_connection.commit()
        return True
    return False