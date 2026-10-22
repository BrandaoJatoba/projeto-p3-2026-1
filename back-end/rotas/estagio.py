from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from db.database import get_db
from db import estagio as crud_estagio
from db.enumStatus import StatusPropostaEstagio, StatusRelatorioEstagio
from schemas import (
    EstagioDocenciaBase,
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
    """
    Cria um novo registro de estágio de docência.
    """
    try:
        estagio = crud_estagio.criar_estagio_docencia(db_connection, dados)
        return estagio
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
    db_connection: Session = Depends(get_db),
    usuario=Depends(autorizar(PERFIS_GESTAO)),
):
    """
    Lista todos os registros de estágio de docência.
    """
    estagios = crud_estagio.listar_estagios_docencia(db_connection)
    return estagios

@router.get(
    "/{id_estagio}",
    response_model=EstagioDocenciaResponse
)
def obter_estagio_docencia(
    id_estagio: int,
    db_connection: Session = Depends(get_db),
    usuario=Depends(autorizar(PERFIS_GESTAO)),
):
    """
    Obtém um registro de estágio de docência pelo ID.
    """
    estagio = crud_estagio.obter_estagio_docencia(db_connection, id_estagio)
    if not estagio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Estágio de docência não encontrado."
        )
    return estagio

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
    """
    Atualiza um registro de estágio de docência pelo ID.
    """
    estagio_existente = crud_estagio.obter_estagio_docencia(db_connection, id_estagio)
    if not estagio_existente:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Estágio de docência não encontrado."
        )

    try:
        estagio_atualizado = crud_estagio.atualizar_estagio_docencia(db_connection, id_estagio, dados)
        return estagio_atualizado
    except IntegrityError:
        db_connection.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Erro ao atualizar o estágio de docência. Verifique os dados fornecidos."
        )
        