from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from db.database import get_db
from db import proficiencia as crud_proficiencia
from schemas import (
    ProficienciaCreate, 
    ProficienciaUpdate, 
    ProficienciaResponse
)
from security import autorizar

router = APIRouter(prefix="/proficiencia", tags=["Proficiencia"])

PERFIS_GESTAO = ["SECRETARIA", "COORDENACAO", "ADMIN"]

@router.post(
    "",
    response_model=ProficienciaResponse,
    status_code=status.HTTP_201_CREATED,
)
def cadastrar_proficiencia(
    dados: ProficienciaCreate,
    db_connection: Session = Depends(get_db),
    usuario=Depends(autorizar(PERFIS_GESTAO)),
):
    """Cadastra uma nova proficiência no sistema."""
    try:
        # CORREÇÃO: Passando os atributos corretos esperados pelo CRUD de Proficiência
        proficiencia = crud_proficiencia.cadastrar_proficiencia(
            db_connection=db_connection, 
            id_estudante=dados.id_estudante,
            status_certificado=dados.status_certificado,
            data_entrega_certificado=dados.data_entrega_certificado,
            consolidada_sigaa=dados.consolidada_sigaa
        )
        return ProficienciaResponse.model_validate(proficiencia)
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Erro de integridade ao cadastrar a proficiência.",
        )

@router.get(
    "",
    response_model=list[ProficienciaResponse],
    status_code=status.HTTP_200_OK,
)
def listar_proficiencias(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200), # CORREÇÃO: Adicionado limit
    db_connection: Session = Depends(get_db),
    usuario=Depends(autorizar(PERFIS_GESTAO)),
):
    """Retorna uma lista paginada de todas as proficiências."""
    proficiencias = crud_proficiencia.listar_proficiencias(db_connection, skip=skip, limit=limit)
    return [ProficienciaResponse.model_validate(p) for p in proficiencias]

@router.get(
    "/{id_proficiencia}",
    response_model=ProficienciaResponse,
    status_code=status.HTTP_200_OK,
)
def buscar_proficiencia_por_id(
    id_proficiencia: int,
    db_connection: Session = Depends(get_db),
    usuario=Depends(autorizar(PERFIS_GESTAO)),
):
    """Busca uma proficiência por ID."""
    proficiencia = crud_proficiencia.buscar_proficiencia_por_id(db_connection, id_proficiencia)
    if not proficiencia:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Proficiência não encontrada.",
        )
    return ProficienciaResponse.model_validate(proficiencia)

@router.put(
    "/{id_proficiencia}",
    response_model=ProficienciaResponse,
    status_code=status.HTTP_200_OK,
)
def atualizar_proficiencia(
    id_proficiencia: int,
    dados: ProficienciaUpdate,
    db_connection: Session = Depends(get_db),
    usuario=Depends(autorizar(PERFIS_GESTAO)),
):
    """Atualiza uma proficiência existente."""
    # CORREÇÃO: Usando model_dump no lugar de dict()
    proficiencia = crud_proficiencia.atualizar_proficiencia(
        db_connection, 
        id_proficiencia, 
        dados.model_dump(exclude_unset=True)
    )
    if not proficiencia:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Proficiência não encontrada.",
        )
    return ProficienciaResponse.model_validate(proficiencia)

@router.delete(
    "/{id_proficiencia}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def deletar_proficiencia(
    id_proficiencia: int,
    db_connection: Session = Depends(get_db),
    usuario=Depends(autorizar(PERFIS_GESTAO)),
):
    """Deleta uma proficiência existente."""
    sucesso = crud_proficiencia.deletar_proficiencia(db_connection, id_proficiencia)
    if not sucesso:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Proficiência não encontrada.",
        )