from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from db.database import get_db
from db import disciplina as crud_disciplina
from schemas import (
    DisciplinaCreate, 
    DisciplinaUpdate, 
    DisciplinaResponse
)
from security import autorizar

PERFIS_GESTAO = ["SECRETARIA", "COORDENACAO", "ADMIN"]

router = APIRouter(prefix="/disciplinas", tags=["Disciplinas"])

@router.post(
    "",
    response_model=DisciplinaResponse,
    status_code=status.HTTP_201_CREATED,
)
def cadastrar_disciplina(
    dados: DisciplinaCreate,
    db_connection: Session = Depends(get_db),
    usuario=Depends(autorizar(PERFIS_GESTAO)),
):
    """Cadastra uma nova disciplina no sistema."""
    try:
        # Passando os novos atributos para o CRUD
        disciplina = crud_disciplina.criar_disciplina(
            db_connection=db_connection, 
            codigo_disciplina=dados.codigo_disciplina,
            nome_disciplina=dados.nome_disciplina,
            grupo_pesquisa=dados.grupo_pesquisa,           # NOVO
            natureza_disciplina=dados.natureza_disciplina, # NOVO
            creditos=dados.creditos,
            eh_obrigatoria=dados.eh_obrigatoria            # NOVO
        )
        return DisciplinaResponse.model_validate(disciplina)
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Erro de integridade ao cadastrar a disciplina.",
        )

@router.get(
    "/{id_disciplina}",
    response_model=DisciplinaResponse,
    status_code=status.HTTP_200_OK,
)   
def buscar_disciplina_por_id(
    id_disciplina: int,
    db_connection: Session = Depends(get_db),
    usuario=Depends(autorizar(PERFIS_GESTAO)),
):
    """Busca uma disciplina pelo ID."""
    disciplina = crud_disciplina.buscar_disciplina_por_id(db_connection, id_disciplina)
    if not disciplina:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Disciplina com ID {id_disciplina} não encontrada.",
        )
    return DisciplinaResponse.model_validate(disciplina)

@router.get(
    "",
    response_model=list[DisciplinaResponse],
    status_code=status.HTTP_200_OK,
)
def listar_disciplinas(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200), # CORREÇÃO: Paginação adicionada
    db_connection: Session = Depends(get_db),
    usuario=Depends(autorizar(PERFIS_GESTAO)),
):
    """Lista todas as disciplinas cadastradas no sistema."""
    # Assumindo que você adicionou o parâmetro limit no listar_disciplinas do CRUD
    disciplinas = crud_disciplina.listar_disciplinas(db_connection, skip=skip, limit=limit)
    return [DisciplinaResponse.model_validate(d) for d in disciplinas]

@router.get(
    "/codigo/{codigo}",
    response_model=DisciplinaResponse, # CORREÇÃO: O CRUD retorna .first(), então é um objeto, não lista
    status_code=status.HTTP_200_OK,
)
def buscar_disciplina_por_codigo(
    codigo: str,
    db_connection: Session = Depends(get_db),
    usuario=Depends(autorizar(PERFIS_GESTAO)),
):
    """Busca uma disciplina pelo código."""
    disciplina = crud_disciplina.buscar_disciplina_por_codigo(db_connection, codigo)
    if not disciplina:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Nenhuma disciplina encontrada com o código {codigo}.",
        )
    return DisciplinaResponse.model_validate(disciplina)

@router.put(
    "/{id_disciplina}",
    response_model=DisciplinaResponse,
    status_code=status.HTTP_200_OK,
)
def atualizar_disciplina(
    id_disciplina: int,
    dados: DisciplinaUpdate,
    db_connection: Session = Depends(get_db),
    usuario=Depends(autorizar(PERFIS_GESTAO)),
):
    """Atualiza os dados de uma disciplina existente."""
    # O próprio CRUD de disciplina pode fazer a busca e verificar se existe
    try:
        # CORREÇÃO: model_dump em vez de dict()
        disciplina_atualizada = crud_disciplina.atualizar_disciplina(
            db_connection=db_connection, 
            id_disciplina=id_disciplina, 
            dados_atualizacao=dados.model_dump(exclude_unset=True)
        )
        
        if not disciplina_atualizada:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Disciplina com ID {id_disciplina} não encontrada.",
            )
            
        return DisciplinaResponse.model_validate(disciplina_atualizada)
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Erro de integridade ao atualizar a disciplina.",
        )

@router.delete(
    "/{id_disciplina}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def deletar_disciplina(
    id_disciplina: int,
    db_connection: Session = Depends(get_db),
    usuario=Depends(autorizar(PERFIS_GESTAO)),
):
    """Deleta uma disciplina pelo seu ID."""
    sucesso = crud_disciplina.deletar_disciplina(db_connection, id_disciplina)
    if not sucesso:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Disciplina com ID {id_disciplina} não encontrada.",)