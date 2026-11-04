from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from db.database import get_db
from db import professor as crud_professor
from schemas import (ProfessorCriacao, ProfessorAtualizacao, ProfessorResposta, ProfessorDetalhado)
from security import autorizar

router = APIRouter(prefix="/professores", tags=["Professores"])

PERFIS_GESTAO = ["SECRETARIA", "COORDENACAO", "ADMIN"]

@router.post(
    "",
    response_model=ProfessorDetalhado,
    status_code=status.HTTP_201_CREATED,
)
def cadastrar_professor(
    dados: ProfessorCriacao,
    db_connection: Session = Depends(get_db),
    usuario=Depends(autorizar(PERFIS_GESTAO)),
):
    """Cadastra um novo professor no sistema."""
    try:
        # CORREÇÃO: Passando o atributo específico (nome) em vez do objeto inteiro
        professor = crud_professor.criar_professor(
            db_connection=db_connection, 
            nome_professor=dados.nome_professor 
        )
        return ProfessorResposta.model_validate(professor)
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Erro de integridade ao cadastrar o professor.",
        )

@router.get(
    "/{id_professor}",
    response_model=ProfessorDetalhado,
    status_code=status.HTTP_200_OK,
)
def buscar_professor_por_id(
    id_professor: int,
    db_connection: Session = Depends(get_db),
    usuario=Depends(autorizar(PERFIS_GESTAO)),
):
    """Busca um professor pelo ID."""
    professor = crud_professor.buscar_professor_por_id(db_connection, id_professor)
    if not professor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Professor com ID {id_professor} não encontrado.",
        )
    return ProfessorResposta.model_validate(professor)

@router.put(
    "/{id_professor}",
    response_model=ProfessorDetalhado,
    status_code=status.HTTP_200_OK,
)
def atualizar_professor(
    id_professor: int,
    dados: ProfessorAtualizacao,
    db_connection: Session = Depends(get_db),
    usuario=Depends(autorizar(PERFIS_GESTAO)),
):
    """Atualiza os dados de um professor existente."""
    try:
        # CORREÇÃO: O próprio CRUD já verifica se existe. 
        # Passamos o ID e o dicionário de dados (usando model_dump).
        professor_atualizado = crud_professor.atualizar_professor(
            db_connection=db_connection, 
            id_professor=id_professor, 
            dados_atualizacao=dados.model_dump(exclude_unset=True)
        )
        
        if not professor_atualizado:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Professor com ID {id_professor} não encontrado.",
            )
            
        return ProfessorResposta.model_validate(professor_atualizado)
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Erro de integridade ao atualizar o professor.",
        )

@router.delete(
    "/{id_professor}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def deletar_professor(
    id_professor: int,
    db_connection: Session = Depends(get_db),
    usuario=Depends(autorizar(PERFIS_GESTAO)),
):
    """Deleta um professor existente."""
    try:
        # CORREÇÃO: Passando o ID em vez do objeto inteiro, e tratando o retorno booleano
        sucesso = crud_professor.deletar_professor(db_connection, id_professor)
        if not sucesso:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Professor com ID {id_professor} não encontrado.",
            )
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Erro de integridade ao deletar o professor. Ele pode estar vinculado a um estudante.",
        )

@router.get(
    "",
    response_model=list[ProfessorDetalhado],
    status_code=status.HTTP_200_OK,
)
def listar_professores(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200), # CORREÇÃO: Paginação via Query Params
    db_connection: Session = Depends(get_db),
    usuario=Depends(autorizar(PERFIS_GESTAO)),
):
    """Lista todos os professores cadastrados."""
    # Assumindo que você ajustou o listar_professores no CRUD para receber 'limit'
    professores = crud_professor.listar_professores(db_connection, skip=skip, limit=limit)
    return [ProfessorResposta.model_validate(professor) for professor in professores]