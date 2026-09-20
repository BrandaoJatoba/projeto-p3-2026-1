from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from db.database import get_db
from db import semestre
from schemas import SemestreCriacao, SemestreResposta, SemestreAtualizacao
from security import autorizar


router = APIRouter(
    prefix="/semestres",
    tags=["Semestres"]
)

@router.post(
    "/",
    response_model=SemestreResposta,
    status_code=status.HTTP_201_CREATED
)
def criar_novo_semestre(
    dados: SemestreCriacao,
    db_connection: Session = Depends(get_db),
    usuario=Depends(autorizar(["SECRETARIA"]))
):
    semestre_existente = semestre.buscar_semestre_por_codigo(
        db_connection,
        dados.codigo_semestre
    )

    if semestre_existente:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Já existe um semestre com esse código."
        )

    try:
        return semestre.criar_semestre(
            db_connection,
            dados.codigo_semestre,
            dados.data_inicio_real,
            dados.data_fim_real,
            dados.dias_letivos
        )
    except IntegrityError:
        db_connection.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Já existe um semestre com esse código."
        )

@router.get(
    "/",
    response_model=list[SemestreResposta]
)
def listar_todos_os_semestres(
    db_connection: Session = Depends(get_db)
):
    return semestre.listar_semestres(db_connection)

@router.get(
    "/{id_semestre}",
    response_model=SemestreResposta
)

def buscar_semestre(
    id_semestre: int,
    db_connection: Session = Depends(get_db)
):
    semestre_encontrado = semestre.buscar_semestre_por_id(
        db_connection,
        id_semestre
    )

    if semestre_encontrado is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Semestre não encontrado."
        )

    return semestre_encontrado

@router.put(
    "/{id_semestre}",
    response_model=SemestreResposta
)

def atualizar_semestre(
    id_semestre: int,
    dados: SemestreAtualizacao,
    db_connection: Session = Depends(get_db),
    usuario=Depends(autorizar(["SECRETARIA"]))
):
    semestre_encontrado = semestre.buscar_semestre_por_id(
        db_connection,
        id_semestre
    )

    if semestre_encontrado is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Semestre não encontrado."
        )

    return semestre.atualizar_semestre(
        db_connection,
        semestre_encontrado,
        dados.data_inicio_real,
        dados.data_fim_real,
        dados.dias_letivos
    )