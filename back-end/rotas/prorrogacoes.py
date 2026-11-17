from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from db.database import get_db
from db import prorrogacoes as crud_prorrogacoes
from schemas import (
    ProrrogacaoCreate,
    ProrrogacaoUpdate,
    ProrrogacaoResponse,
)
from security import autorizar
from services.prazos_service import aplicar_prorrogacao_individual # Importação do serviço

router = APIRouter(prefix="/prorrogacoes", tags=["Prorrogações"])

PERFIS_GESTAO = ["SECRETARIA", "COORDENACAO", "ADMIN"]


@router.post(
    "",
    response_model=ProrrogacaoResponse,
    status_code=status.HTTP_201_CREATED,
)
def criar_prorrogacao(
    dados: ProrrogacaoCreate,
    db_connection: Session = Depends(get_db),
    usuario=Depends(autorizar(PERFIS_GESTAO)),
):
    """Cria um novo pedido de prorrogação de prazo."""
    try:
        nova_prorrogacao = crud_prorrogacoes.criar_prorrogacao(db_connection, dados)
        
        # Gatilho: Recalcula os prazos do aluno afetado caso já nasça aprovada
        aplicar_prorrogacao_individual(db_connection, nova_prorrogacao.id_estudante)
        
        return nova_prorrogacao
    except IntegrityError:
        db_connection.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Erro ao cadastrar a prorrogação. Verifique se o ID do estudante é válido."
        )


@router.get(
    "",
    response_model=list[ProrrogacaoResponse],
)
def listar_prorrogacoes(
    skip: int = 0,
    limit: int = 100,
    db_connection: Session = Depends(get_db),
    usuario=Depends(autorizar(PERFIS_GESTAO)),
):
    """Lista todos os pedidos de prorrogação com paginação."""
    return crud_prorrogacoes.obter_prorrogacoes(db_connection, skip=skip, limit=limit)


@router.get(
    "/{id_prorrogacao}",
    response_model=ProrrogacaoResponse,
)
def obter_prorrogacao(
    id_prorrogacao: int,
    db_connection: Session = Depends(get_db),
    usuario=Depends(autorizar(PERFIS_GESTAO)),
):
    """Obtém os detalhes de uma prorrogação pelo seu ID."""
    prorrogacao = crud_prorrogacoes.obter_prorrogacao_por_id(db_connection, id_prorrogacao)
    if not prorrogacao:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prorrogação não encontrada."
        )
    return prorrogacao


@router.get(
    "/estudante/{id_estudante}",
    response_model=list[ProrrogacaoResponse],
)
def listar_prorrogacoes_por_estudante(
    id_estudante: int,
    db_connection: Session = Depends(get_db),
    usuario=Depends(autorizar(PERFIS_GESTAO)),
):
    """Lista todas as prorrogações solicitadas por um estudante específico."""
    return crud_prorrogacoes.obter_prorrogacoes_por_estudante(db_connection, id_estudante)


@router.put(
    "/{id_prorrogacao}",
    response_model=ProrrogacaoResponse,
)
def atualizar_prorrogacao(
    id_prorrogacao: int,
    dados: ProrrogacaoUpdate,
    db_connection: Session = Depends(get_db),
    usuario=Depends(autorizar(PERFIS_GESTAO)),
):
    """Atualiza o resultado ou dados de uma solicitação de prorrogação."""
    try:
        prorrogacao_atualizada = crud_prorrogacoes.atualizar_prorrogacao(
            db_connection, id_prorrogacao, dados
        )
        if not prorrogacao_atualizada:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Prorrogação não encontrada."
            )
            
        # Gatilho: Recalcula se o status mudou para aprovado ou se os meses mudaram
        aplicar_prorrogacao_individual(db_connection, prorrogacao_atualizada.id_estudante)
        
        return prorrogacao_atualizada
    except IntegrityError:
        db_connection.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Erro ao atualizar a prorrogação. Verifique os dados fornecidos."
        )


@router.delete(
    "/{id_prorrogacao}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def deletar_prorrogacao(
    id_prorrogacao: int,
    db_connection: Session = Depends(get_db),
    usuario=Depends(autorizar(PERFIS_GESTAO)),
):
    """Remove um registro de prorrogação pelo ID."""
    
    # 1. Busca primeiro a prorrogação para saber de qual estudante ela é
    prorrogacao = crud_prorrogacoes.obter_prorrogacao_por_id(db_connection, id_prorrogacao)
    if not prorrogacao:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prorrogação não encontrada."
        )
        
    id_estudante = prorrogacao.id_estudante
    
    # 2. Deleta o registro
    sucesso = crud_prorrogacoes.deletar_prorrogacao(db_connection, id_prorrogacao)
    if not sucesso:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Erro ao deletar a prorrogação."
        )
        
    # 3. Gatilho: Recalcula as datas do estudante subtraindo essa prorrogação
    aplicar_prorrogacao_individual(db_connection, id_estudante)
    
    return None