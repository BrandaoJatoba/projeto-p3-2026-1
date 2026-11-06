from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from db.database import get_db
from db import dissertacao as crud_dissertacao
from schemas import (
    DissertacaoCreate, 
    DissertacaoUpdate, 
    DissertacaoResponse
)
from security import autorizar

PERFIS_GESTAO = ["SECRETARIA", "COORDENACAO", "ADMIN"]

router = APIRouter(prefix="/dissertacoes", tags=["Dissertações"])

@router.post(
    "",
    response_model=DissertacaoResponse,
    status_code=status.HTTP_201_CREATED,
)
def cadastrar_dissertacao(
    dados: DissertacaoCreate,
    db_connection: Session = Depends(get_db),
    usuario=Depends(autorizar(PERFIS_GESTAO)),
):
    """Cadastra uma nova dissertação no sistema."""
    try:
        dissertacao = crud_dissertacao.criar_dissertacao(db_connection, dados)
        return DissertacaoResponse.model_validate(dissertacao)
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Erro de integridade ao cadastrar a dissertação.",
        )

@router.get(
    "/{id_dissertacao}",
    response_model=DissertacaoResponse,
)
def obter_dissertacao(
    id_dissertacao: int,
    db_connection: Session = Depends(get_db),
    usuario=Depends(autorizar(PERFIS_GESTAO)),
):
    """Obtém os detalhes de uma dissertação específica pelo seu ID."""
    dissertacao = crud_dissertacao.obter_dissertacao_por_id(db_connection, id_dissertacao)
    if not dissertacao:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dissertação não encontrada.",
        )
    return DissertacaoResponse.model_validate(dissertacao)

@router.get(
    "",
    response_model=list[DissertacaoResponse],
)
def listar_dissertacoes(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1),
    db_connection: Session = Depends(get_db),
    usuario=Depends(autorizar(PERFIS_GESTAO)),
):
    """Lista todas as dissertações cadastradas no sistema."""
    dissertacoes = crud_dissertacao.listar_dissertacoes(db_connection, skip=skip, limit=limit)
    return [DissertacaoResponse.model_validate(d) for d in dissertacoes]

@router.get(
    "/aluno/{id_estudante}",
    response_model=list[DissertacaoResponse],
)
def listar_dissertacoes_por_aluno(
    id_estudante: int,
    db_connection: Session = Depends(get_db),
    usuario=Depends(autorizar(PERFIS_GESTAO)),
):
    """Lista todas as dissertações de um aluno específico."""
    dissertacoes = crud_dissertacao.listar_dissertacoes_por_aluno(db_connection, id_estudante)
    return [DissertacaoResponse.model_validate(d) for d in dissertacoes]

@router.put(
    "/{id_dissertacao}",
    response_model=DissertacaoResponse,
)  
def atualizar_dissertacao(
    id_dissertacao: int,
    dados: DissertacaoUpdate,
    db_connection: Session = Depends(get_db),
    usuario=Depends(autorizar(PERFIS_GESTAO)),
):
    """Atualiza os detalhes de uma dissertação existente."""
    dissertacao_atualizada = crud_dissertacao.atualizar_dissertacao(db_connection, id_dissertacao, dados)
    if not dissertacao_atualizada:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dissertação não encontrada para atualização.",
        )
    return DissertacaoResponse.model_validate(dissertacao_atualizada)

def deletar_dissertacao(
    id_dissertacao: int,
    db_connection: Session = Depends(get_db),
    usuario=Depends(autorizar(PERFIS_GESTAO)),
):
    """Deleta uma dissertação existente."""
    sucesso = crud_dissertacao.deletar_dissertacao(db_connection, id_dissertacao)
    if not sucesso:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Dissertação não encontrada para deleção.",
        )
    return {"detail": "Dissertação deletada com sucesso."}

