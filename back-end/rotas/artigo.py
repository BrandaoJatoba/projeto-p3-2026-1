from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from db.database import get_db
from db import submissaoartigo as crud_artigo
from schemas import (
    SubmissaoArtigoCreate,
    SubmissaoArtigoUpdate,
    SubmissaoArtigoResponse,
)
from security import autorizar

router = APIRouter(prefix="/artigos", tags=["Submissões de Artigos"])

PERFIS_GESTAO = ["SECRETARIA", "COORDENACAO", "ADMIN"]


@router.post(
    "",
    response_model=SubmissaoArtigoResponse,
    status_code=status.HTTP_201_CREATED,
)
def criar_submissao_artigo(
    dados: SubmissaoArtigoCreate,
    db_connection: Session = Depends(get_db),
    usuario=Depends(autorizar(PERFIS_GESTAO)),
):
    """Cria uma nova submissão de artigo."""
    try:
        return crud_artigo.criar_submissao_artigo(db_connection, dados)
    except IntegrityError:
        db_connection.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Erro ao cadastrar a submissão do artigo. Verifique os dados fornecidos."
        )


@router.get(
    "",
    response_model=list[SubmissaoArtigoResponse],
)
def listar_submissoes_artigos(
    skip: int = 0,
    limit: int = 100,
    db_connection: Session = Depends(get_db),
    usuario=Depends(autorizar(PERFIS_GESTAO)),
):
    """Lista todas as submissões de artigos com suporte à paginação."""
    return crud_artigo.obter_submissoes_artigos(db_connection, skip=skip, limit=limit)


@router.get(
    "/{id_artigo}",
    response_model=SubmissaoArtigoResponse,
)
def obter_submissao_artigo(
    id_artigo: int,
    db_connection: Session = Depends(get_db),
    usuario=Depends(autorizar(PERFIS_GESTAO)),
):
    """Obtém uma submissão de artigo pelo ID do artigo."""
    submissao = crud_artigo.obter_submissao_artigo_por_id(db_connection, id_artigo)
    if not submissao:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Submissão de artigo não encontrada."
        )
    return submissao


@router.put(
    "/{id_artigo}",
    response_model=SubmissaoArtigoResponse,
)
def atualizar_submissao_artigo(
    id_artigo: int,
    dados: SubmissaoArtigoUpdate,
    db_connection: Session = Depends(get_db),
    usuario=Depends(autorizar(PERFIS_GESTAO)),
):
    """Atualiza parcialmente ou integralmente os dados de uma submissão existente."""
    try:
        submissao_atualizada = crud_artigo.atualizar_submissao_artigo(
            db_connection, id_artigo, dados
        )
        if not submissao_atualizada:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Submissão de artigo não encontrada."
            )
        return submissao_atualizada
    except IntegrityError:
        db_connection.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Erro ao atualizar a submissão de artigo. Verifique os dados fornecidos."
        )


@router.delete(
    "/{id_submissao}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def deletar_submissao_artigo(
    id_submissao: int,
    db_connection: Session = Depends(get_db),
    usuario=Depends(autorizar(PERFIS_GESTAO)),
):
    """Remove um registro de submissão de artigo pelo ID da submissão."""
    sucesso = crud_artigo.deletar_submissao_artigo(db_connection, id_submissao)
    if not sucesso:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Submissão de artigo não encontrada."
        )
    return None