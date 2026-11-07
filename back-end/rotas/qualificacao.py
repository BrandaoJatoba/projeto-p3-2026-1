from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from db.database import get_db
from db import qualificacao as crud_qualificacao
from schemas import (
    QualificacaoCreate, 
    QualificacaoUpdate, 
    QualificacaoResponse
)
from security import autorizar

PERFIS_GESTAO = ["SECRETARIA", "COORDENACAO", "ADMIN"]

router = APIRouter(prefix="/qualificacoes", tags=["Qualificações"])

@router.post(
    "",
    response_model=QualificacaoResponse,
    status_code=status.HTTP_201_CREATED,
)
def cadastrar_qualificacao(
    dados: QualificacaoCreate,
    db_connection: Session = Depends(get_db),
    usuario=Depends(autorizar(PERFIS_GESTAO)),
):
    """Cadastra uma nova qualificação no sistema."""
    try:
        qualificacao = crud_qualificacao.criar_qualificacao(db_connection,
                                                            id_dissertacao=dados.id_dissertacao,
                                                            prazo_maximo_qualificacao=dados.prazo_maximo_qualificacao,
                                                            data_realizacao=dados.data_realizacao,
                                                            status_qualificacao=dados.status_qualificacao,
                                                            retorno_qualificacao=dados.retorno_qualificacao,
                                                            tentativa = dados.tentativa,
                                                            )
        return QualificacaoResponse.model_validate(qualificacao)
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Erro de integridade ao cadastrar a qualificação.",
        )

@router.get(
    "",
    response_model=list[QualificacaoResponse],
)
def listar_qualificacoes(
    db_connection: Session = Depends(get_db),
    usuario=Depends(autorizar(PERFIS_GESTAO)),
):
    """Lista todas as qualificações cadastradas no sistema."""
    qualificacoes = crud_qualificacao.listar_qualificacoes(db_connection)
    return [QualificacaoResponse.model_validate(q) for q in qualificacoes]

@router.get(
    "/{id_qualificacao}",
    response_model=QualificacaoResponse,
)
def obter_qualificacao(
    id_qualificacao: int,
    db_connection: Session = Depends(get_db),
    usuario=Depends(autorizar(PERFIS_GESTAO)),
):
    """Obtém os detalhes de uma qualificação específica pelo seu ID."""
    qualificacao = crud_qualificacao.obter_qualificacao_por_id(db_connection, id_qualificacao)
    if not qualificacao:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Qualificação não encontrada.",
        )
    return QualificacaoResponse.model_validate(qualificacao)

@router.get(
    "/estudante/{id_estudante}",
    response_model=list[QualificacaoResponse],
)
def listar_qualificacoes_por_aluno(
    id_estudante: int,
    db_connection: Session = Depends(get_db),
    usuario=Depends(autorizar(PERFIS_GESTAO)),
):
    """Lista todas as qualificações de um aluno específico."""
    qualificacoes = crud_qualificacao.listar_qualificacoes_por_aluno(db_connection, id_estudante)
    return [QualificacaoResponse.model_validate(q) for q in qualificacoes]

@router.put(
    "/{id_qualificacao}",
    response_model=QualificacaoResponse,
)
def atualizar_qualificacao(
    id_qualificacao: int,
    atualizacoes: QualificacaoUpdate,
    db_connection: Session = Depends(get_db),
    usuario=Depends(autorizar(PERFIS_GESTAO)),
):
    """Atualiza os detalhes de uma qualificação existente."""
    qualificacao_atualizada = crud_qualificacao.atualizar_qualificacao(
        db_connection, id_qualificacao, atualizacoes.model_dump(exclude_unset=True)
    )
    if not qualificacao_atualizada:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Qualificação não encontrada para atualização.",
        )
    return QualificacaoResponse.model_validate(qualificacao_atualizada)

@router.delete(
    "/{id_qualificacao}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def deletar_qualificacao(
    id_qualificacao: int,
    db_connection: Session = Depends(get_db),
    usuario=Depends(autorizar(PERFIS_GESTAO)),
):
    """Deleta uma qualificação existente pelo seu ID."""
    sucesso = crud_qualificacao.deletar_qualificacao(db_connection, id_qualificacao)
    if not sucesso:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Qualificação não encontrada para deleção.",
        )
