from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from db.database import get_db
from db import estagiodocencia as crud_estagio
from schemas import (
    EstagioDocenciaCreate,
    EstagioDocenciaUpdate,
    EstagioDocenciaResponse
)
from security import autorizar

router = APIRouter(prefix="/estagios", tags=["Estágios"])

PERFIS_GESTAO = ["SECRETARIA", "COORDENACAO", "ADMIN"]


@router.post(
    "",
    response_model=EstagioDocenciaResponse,
    status_code=status.HTTP_201_CREATED
)
def criar_estagio_docencia(
    dados: EstagioDocenciaCreate,
    db_connection: Session = Depends(get_db),
    usuario=Depends(autorizar(PERFIS_GESTAO)),
):
    """Cria um novo registro de estágio de docência."""
    try:
        return crud_estagio.criar_estagio_docencia(db_connection, dados)
    except IntegrityError:
        db_connection.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Erro ao criar o estágio de docência. Verifique os dados fornecidos."
        )


@router.get(
    "",
    response_model=list[EstagioDocenciaResponse]
)
def listar_estagios_docencia(
    skip: int = 0,
    limit: int = 100,
    db_connection: Session = Depends(get_db),
    usuario=Depends(autorizar(PERFIS_GESTAO)),
):
    """Lista todos os registros de estágio de docência."""
    return crud_estagio.listar_estagios_docencia(db_connection, skip=skip, limit=limit)


@router.get(
    "/{id_estagio}",
    response_model=EstagioDocenciaResponse
)
def obter_estagio_docencia(
    id_estagio: int,
    db_connection: Session = Depends(get_db),
    usuario=Depends(autorizar(PERFIS_GESTAO)),
):
    """Obtém um registro de estágio de docência pelo ID."""
    estagio = crud_estagio.buscar_estagio_por_id(db_connection, id_estagio)
    if not estagio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Estágio de docência não encontrado."
        )
    return estagio


@router.get(
    "/estudante/{id_estudante}",
    response_model=list[EstagioDocenciaResponse]
)
def listar_estagios_por_estudante(
    id_estudante: int,
    db_connection: Session = Depends(get_db),
    usuario=Depends(autorizar(PERFIS_GESTAO)),
):
    """Lista os estágios de docência de um estudante específico."""
    return crud_estagio.buscar_estagios_por_estudante(db_connection, id_estudante)


@router.put(
    "/{id_estagio}",
    response_model=EstagioDocenciaResponse
)
def atualizar_estagio_docencia(
    id_estagio: int,
    dados: EstagioDocenciaUpdate,
    db_connection: Session = Depends(get_db),
    usuario=Depends(autorizar(PERFIS_GESTAO)),
):
    """Atualiza um registro de estágio de docência pelo ID."""
    estagio_existente = crud_estagio.buscar_estagio_por_id(db_connection, id_estagio)
    if not estagio_existente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Estágio de docência não encontrado."
        )

    try:
        return crud_estagio.atualizar_estagio_docencia(db_connection, id_estagio, dados)
    except IntegrityError:
        db_connection.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Erro ao atualizar o estágio de docência. Verifique os dados fornecidos."
        )


@router.delete(
    "/{id_estagio}",
    status_code=status.HTTP_204_NO_CONTENT
)
def deletar_estagio_docencia(
    id_estagio: int,
    db_connection: Session = Depends(get_db),
    usuario=Depends(autorizar(PERFIS_GESTAO)),
):
    """Remove um registro de estágio de docência pelo ID."""
    sucesso = crud_estagio.deletar_estagio_docencia(db_connection, id_estagio)
    if not sucesso:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Estágio de docência não encontrado."
        )
    return None