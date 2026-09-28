from typing import List, Optional
from sqlalchemy.orm import Session
from db import models
import schemas


def criar_estagio_docencia(
    db_connection: Session, 
    estagio_in: schemas.EstagioDocenciaCreate
) -> models.EstagioDocencia:
    """Cria um novo registro de estágio docência."""
    novo_estagio = models.EstagioDocencia(**estagio_in.model_dump())
    db_connection.add(novo_estagio)
    db_connection.commit()
    db_connection.refresh(novo_estagio)
    return novo_estagio


def listar_estagios_docencia(
    db_connection: Session, 
    skip: int = 0, 
    limit: int = 100
) -> List[models.EstagioDocencia]:
    """Retorna uma lista paginada de todos os estágios docência."""
    return db_connection.query(models.EstagioDocencia).offset(skip).limit(limit).all()


def buscar_estagio_por_id(
    db_connection: Session, 
    id_estagio: int
) -> Optional[models.EstagioDocencia]:
    """Busca um estágio docência pelo seu ID."""
    return (
        db_connection.query(models.EstagioDocencia)
        .filter(models.EstagioDocencia.id_estagio == id_estagio)
        .first()
    )


def buscar_estagios_por_estudante(
    db_connection: Session, 
    id_estudante: int
) -> List[models.EstagioDocencia]:
    """Busca todos os estágios registrados para um determinado estudante."""
    return (
        db_connection.query(models.EstagioDocencia)
        .filter(models.EstagioDocencia.id_estudante == id_estudante)
        .all()
    )


def atualizar_estagio_docencia(
    db_connection: Session, 
    id_estagio: int, 
    dados_atualizacao: schemas.EstagioDocenciaUpdate
) -> Optional[models.EstagioDocencia]:
    """Atualiza campos específicos de um estágio docência existente."""
    estagio = buscar_estagio_por_id(db_connection, id_estagio)
    if not estagio:
        return None

    # Extrai apenas os campos explicitamente alterados na requisição
    dados_dict = dados_atualizacao.model_dump(exclude_unset=True)

    for chave, valor in dados_dict.items():
        setattr(estagio, chave, valor)

    db_connection.commit()
    db_connection.refresh(estagio)
    return estagio


def deletar_estagio_docencia(db_connection: Session, id_estagio: int) -> bool:
    """Deleta um estágio docência pelo ID."""
    estagio = buscar_estagio_por_id(db_connection, id_estagio)
    if not estagio:
        return False

    db_connection.delete(estagio)
    db_connection.commit()
    return True