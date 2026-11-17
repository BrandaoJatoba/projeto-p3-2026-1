from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from typing import List
from db.database import get_db
from db import historicodisciplina as crud_historicodisciplina
from schemas import (
    HistoricoDisciplinaCreate, 
    HistoricoDisciplinaUpdate, 
    HistoricoDisciplinaResponse
)
from security import autorizar

PERFIS_GESTAO = ["SECRETARIA", "COORDENACAO", "ADMIN"]

router = APIRouter(prefix="/historico-disciplinas", tags=["Histórico de Disciplinas"])
@router.post(
    "", 
    response_model=HistoricoDisciplinaResponse, 
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(autorizar(PERFIS_GESTAO))]
)
def criar_historico(
    historico_in: HistoricoDisciplinaCreate,
    db: Session = Depends(get_db)
):
    """
    Registra uma nova disciplina no histórico do estudante.
    """
    try:
        novo_historico = crud_historicodisciplina.criar_historico_disciplina(db, historico_in)
        return novo_historico
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Erro de integridade. Verifique se os IDs do estudante, disciplina e semestre são válidos."
        )


@router.put(
    "/{id_historico}", 
    response_model=HistoricoDisciplinaResponse,
    dependencies=[Depends(autorizar(PERFIS_GESTAO))]
)
def atualizar_historico(
    id_historico: int,
    atualizacoes: HistoricoDisciplinaUpdate,
    db: Session = Depends(get_db)
):
    """
    Atualiza um registro existente no histórico de disciplinas (ex: atualizar o conceito ou status).
    """
    try:
        historico_atualizado = crud_historicodisciplina.atualizar_historico_disciplina(
            db, 
            id_historico, 
            atualizacoes
        )
        if not historico_atualizado:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Registro de histórico não encontrado."
            )
        return historico_atualizado
    
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Erro de integridade ao atualizar os dados. Verifique se as chaves estrangeiras são válidas."
        )

@router.get(
    "/estudante/{id_estudante}", 
    response_model=List[HistoricoDisciplinaResponse],
    dependencies=[Depends(autorizar(PERFIS_GESTAO))] # Se o discente puder ver, adicione "DISCENTE" à lista de perfis autorizados
)
def listar_historico_estudante(
    id_estudante: int, 
    db: Session = Depends(get_db)
):
    """
    Retorna todo o histórico de disciplinas cursadas por um estudante específico.
    """
    registros = crud_historicodisciplina.buscar_historicos_por_estudante(db, id_estudante)
    return registros


@router.delete(
    "/{id_historico}", 
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(autorizar(PERFIS_GESTAO))]
)
def deletar_historico(
    id_historico: int, 
    db: Session = Depends(get_db)
):
    """
    Remove um registro do histórico de disciplinas do estudante.
    """
    sucesso = crud_historicodisciplina.deletar_historico_disciplina(db, id_historico)
    if not sucesso:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Registro de histórico não encontrado."
        )