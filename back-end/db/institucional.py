from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from datetime import date
import models

# ==========================================
# CRUD: SEMESTRE LETIVO
# ==========================================

def criar_semestre_letivo(
    db: Session, 
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
    db.add(novo_semestre)
    db.commit()
    db.refresh(novo_semestre)
    return novo_semestre

def buscar_semestre_letivo(db: Session, id_semestre: int) -> Optional[models.SemestreLetivo]:
    """Retorna um semestre letivo específico pelo ID."""
    return db.query(models.SemestreLetivo).filter(models.SemestreLetivo.id_semestre == id_semestre).first()

def listar_semestres_letivos(db: Session, skip: int = 0, limit: int = 100) -> List[models.SemestreLetivo]:
    """Retorna uma lista paginada de todos os semestres letivos."""
    return db.query(models.SemestreLetivo).offset(skip).limit(limit).all()

def atualizar_semestre_letivo(db: Session, id_semestre: int, dados_atualizacao: Dict[str, Any]) -> Optional[models.SemestreLetivo]:
    """Atualiza campos específicos de um semestre letivo existente."""
    semestre = buscar_semestre_letivo(db, id_semestre)
    if not semestre:
        return None
        
    for chave, valor in dados_atualizacao.items():
        if hasattr(semestre, chave):
            setattr(semestre, chave, valor)
            
    db.commit()
    db.refresh(semestre)
    return semestre

def deletar_semestre_letivo(db: Session, id_semestre: int) -> bool:
    """Remove um semestre letivo pelo ID."""
    semestre = buscar_semestre_letivo(db, id_semestre)
    if semestre:
        db.delete(semestre)
        db.commit()
        return True
    return False


# ==========================================
# CRUD: SUSPENSÃO DE CALENDÁRIO
# ==========================================

def criar_suspensao_calendario(
    db: Session, 
    id_semestre: int, 
    data_inicio_suspensao: date, 
    motivo: Optional[str] = None, 
    data_fim_suspensao: Optional[date] = None, 
    dias_suspensos: Optional[int] = None
) -> models.SuspensaoCalendario:
    """Registra uma nova suspensão associada a um semestre letivo."""
    nova_suspensao = models.SuspensaoCalendario(
        id_semestre=id_semestre,
        motivo=motivo,
        data_inicio_suspensao=data_inicio_suspensao,
        data_fim_suspensao=data_fim_suspensao,
        dias_suspensos=dias_suspensos
    )
    db.add(nova_suspensao)
    db.commit()
    db.refresh(nova_suspensao)
    return nova_suspensao

def buscar_suspensao(db: Session, id_suspensao: int) -> Optional[models.SuspensaoCalendario]:
    """Retorna os dados de uma paralisação específica."""
    return db.query(models.SuspensaoCalendario).filter(models.SuspensaoCalendario.id_suspensao == id_suspensao).first()

def listar_suspensoes_por_semestre(db: Session, id_semestre: int) -> List[models.SuspensaoCalendario]:
    """Lista todas as suspensões vinculadas a um determinado semestre letivo."""
    return db.query(models.SuspensaoCalendario).filter(models.SuspensaoCalendario.id_semestre == id_semestre).all()

def atualizar_suspensao(db: Session, id_suspensao: int, dados_atualizacao: Dict[str, Any]) -> Optional[models.SuspensaoCalendario]:
    """Atualiza informações de uma suspensão (ex: adicionar data de fim)."""
    suspensao = buscar_suspensao(db, id_suspensao)
    if not suspensao:
        return None
        
    for chave, valor in dados_atualizacao.items():
        if hasattr(suspensao, chave):
            setattr(suspensao, chave, valor)
            
    db.commit()
    db.refresh(suspensao)
    return suspensao

def deletar_suspensao(db: Session, id_suspensao: int) -> bool:
    """Remove o registro de uma suspensão."""
    suspensao = buscar_suspensao(db, id_suspensao)
    if suspensao:
        db.delete(suspensao)
        db.commit()
        return True
    return False


