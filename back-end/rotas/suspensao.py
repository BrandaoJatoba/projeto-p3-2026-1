from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from db.database import get_db
from db import suspensao  # Módulo com as funções CRUD geradas anteriormente
from schemas import SuspensaoCalendarioCreate, SuspensaoCalendarioUpdate, SuspensaoCalendarioResponse
from security import autorizar

router = APIRouter(prefix="/configuracoes/suspensoes", tags=["Suspensoes"])

@router.post("", response_model=SuspensaoCalendarioResponse, status_code=status.HTTP_201_CREATED)
def criar_suspensao(
    dados: SuspensaoCalendarioCreate,
    db: Session = Depends(get_db),
    usuario_atual = Depends(autorizar(["ADMIN", "COORDENACAO"]))
):
    nova_suspensao = suspensao.criar_suspensao_calendario(db=db, **dados.model_dump())
    return nova_suspensao

@router.get("", response_model=List[SuspensaoCalendarioResponse])
def listar_todas_suspensoes(
    db: Session = Depends(get_db),
    usuario_atual = Depends(autorizar(["ADMIN", "COORDENACAO", "SECRETARIA", "DISCENTE"]))
):
    # Pode ser necessário adicionar essa função simples no seu db/suspensao.py: 
    # return db.query(models.SuspensaoCalendario).all()
    registros = suspensao.listar_todas_suspensoes(db=db)
    return registros

@router.get("/{id_suspensao}", response_model=SuspensaoCalendarioResponse)
def obter_suspensao_por_id(
    id_suspensao: int,
    db: Session = Depends(get_db),
    usuario_atual = Depends(autorizar(["ADMIN", "COORDENACAO", "SECRETARIA", "DISCENTE"]))
):
    registro = suspensao.buscar_suspensao(db=db, id_suspensao=id_suspensao)
    if not registro:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Suspensão não encontrada.")
    return registro

@router.put("/{id_suspensao}", response_model=SuspensaoCalendarioResponse)
def atualizar_suspensao(
    id_suspensao: int,
    dados: SuspensaoCalendarioUpdate,
    db: Session = Depends(get_db),
    usuario_atual = Depends(autorizar(["ADMIN", "COORDENACAO"]))
):
    # exclude_unset=True garante que apenas os campos enviados no JSON sejam atualizados
    dados_atualizacao = dados.model_dump(exclude_unset=True)
    
    registro_atualizado = suspensao.atualizar_suspensao(
        db=db, 
        id_suspensao=id_suspensao, 
        dados_atualizacao=dados_atualizacao
    )
    
    if not registro_atualizado:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Suspensão não encontrada para atualização.")
    
    return registro_atualizado

@router.delete("/{id_suspensao}", status_code=status.HTTP_204_NO_CONTENT)
def deletar_suspensao_rota(
    id_suspensao: int,
    db: Session = Depends(get_db),
    usuario_atual = Depends(autorizar(["ADMIN"]))
):
    sucesso = suspensao.deletar_suspensao(db=db, id_suspensao=id_suspensao)
    if not sucesso:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Suspensão não encontrada para exclusão.")
    return None