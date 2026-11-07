from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from db.database import get_db
from db import defesa as crud_defesa
from schemas import (
    DefesaCreate, 
    DefesaUpdate, 
    DefesaResponse
)
from security import autorizar

PERFIS_GESTAO = ["SECRETARIA", "COORDENACAO", "ADMIN"]

router = APIRouter(prefix="/defesas", tags=["Defesas"])

@router.post(
    "",
    response_model=DefesaResponse,
    status_code=status.HTTP_201_CREATED,
)
def cadastrar_defesa(
    dados: DefesaCreate,
    db_connection: Session = Depends(get_db),
    usuario=Depends(autorizar(PERFIS_GESTAO)),
):
    """Cadastra uma nova defesa no sistema."""
    try:
        defesa = crud_defesa.criar_defesa(db_connection,
                                          id_dissertacao=dados.id_dissertacao,
                                          prazo_solicitacao_homologacao_banca=dados.prazo_solicitacao_homologacao_banca,
                                          data_solicitacao_banca=dados.data_solicitacao_banca,
                                          status_homologacao_banca=dados.status_homologacao_banca,
                                          prazo_maximo_defesa=dados.prazo_maximo_defesa,
                                          data_realizacao=dados.data_realizacao,
                                          status_defesa=dados.status_defesa,
                                          retorno_defesa=dados.retorno_defesa,
                                          conceito_defesa=dados.conceito_defesa,
                                          prazo_versao_final=dados.prazo_versao_final,
                                          prazo_limite_processo_diploma=dados.prazo_limite_processo_diploma,
                                          status_processo_diploma=dados.status_processo_diploma)
        return DefesaResponse.model_validate(defesa)
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Erro de integridade ao cadastrar a defesa.",
        )

@router.get(
    "/{id_defesa}",
    response_model=DefesaResponse,
)
def obter_defesa(
    id_defesa: int,
    db_connection: Session = Depends(get_db),
    usuario=Depends(autorizar(PERFIS_GESTAO)),
):
    """Obtém os detalhes de uma defesa específica pelo seu ID."""
    defesa = crud_defesa.obter_defesa_por_id(db_connection, id_defesa)
    if not defesa:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Defesa não encontrada.",
        )
    return DefesaResponse.model_validate(defesa)

@router.get(
    "",
    response_model=list[DefesaResponse],
)
def listar_defesas(
    db_connection: Session = Depends(get_db),
    usuario=Depends(autorizar(PERFIS_GESTAO)),
):
    """Lista todas as defesas cadastradas no sistema."""
    defesas = crud_defesa.listar_defesas(db_connection)
    return [DefesaResponse.model_validate(defesa) for defesa in defesas]

@router.get(
    "/dissertacao/{id_dissertacao}",
    response_model=DefesaResponse,
)
def obter_defesa_por_dissertacao(
    id_dissertacao: int,
    db_connection: Session = Depends(get_db),
    usuario=Depends(autorizar(PERFIS_GESTAO)),
):
    """Obtém a defesa associada a uma dissertação específica pelo ID da dissertação."""
    defesa = crud_defesa.obter_defesa_por_dissertacao(db_connection, id_dissertacao)
    if not defesa:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Defesa não encontrada para a dissertação especificada.",
        )
    return DefesaResponse.model_validate(defesa)

@router.get("/estudante/{id_estudante}", response_model=list[DefesaResponse])
def obter_defesas_por_aluno(
    id_estudante: int,
    db_connection: Session = Depends(get_db),
    usuario=Depends(autorizar(PERFIS_GESTAO)),
):
    """Obtém todas as defesas associadas a um aluno específico pelo ID do aluno."""
    defesas = crud_defesa.obter_defesas_por_aluno(db_connection, id_estudante)
    return [DefesaResponse.model_validate(defesa) for defesa in defesas]

@router.put(
    "/{id_defesa}",
    response_model=DefesaResponse,
)
def atualizar_defesa(
    id_defesa: int,
    atualizacoes: DefesaUpdate,
    db_connection: Session = Depends(get_db),
    usuario=Depends(autorizar(PERFIS_GESTAO)),
):
    """Atualiza os detalhes de uma defesa específica pelo seu ID."""
    defesa_atualizada = crud_defesa.atualizar_defesa(db_connection, id_defesa, atualizacoes.model_dump(exclude_unset=True))
    if not defesa_atualizada:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Defesa não encontrada para atualização.",
        )
    return DefesaResponse.model_validate(defesa_atualizada)

@router.delete(
    "/{id_defesa}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def deletar_defesa(
    id_defesa: int,
    db_connection: Session = Depends(get_db),
    usuario=Depends(autorizar(PERFIS_GESTAO)),
):
    """Deleta uma defesa específica pelo seu ID."""
    sucesso = crud_defesa.deletar_defesa(db_connection, id_defesa)
    if not sucesso:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Defesa não encontrada para deleção.",
        )