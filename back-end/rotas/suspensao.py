from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from db.database import get_db
from db import suspensao  # Módulo com as funções CRUD geradas anteriormente
from schemas import SuspensaoCalendarioCreate, SuspensaoCalendarioUpdate, SuspensaoCalendarioResponse
from security import autorizar
from services.prazos_service import aplicar_suspensao_global # Importação do serviço

router = APIRouter(prefix="/configuracoes/suspensoes", tags=["Suspensoes"])

@router.post("", response_model=SuspensaoCalendarioResponse, status_code=status.HTTP_201_CREATED)
def criar_suspensao(
    dados: SuspensaoCalendarioCreate,
    db: Session = Depends(get_db),
    usuario_atual = Depends(autorizar(["ADMIN", "COORDENACAO"]))
):
    nova_suspensao = suspensao.criar_suspensao_calendario(db=db, **dados.model_dump())
    
    # Caso 1: Cadastrada com dados completos (início e fim)
    if nova_suspensao.data_inicio_suspensao and nova_suspensao.data_fim_suspensao:
        aplicar_suspensao_global(db)
        
    return nova_suspensao

@router.get("", response_model=List[SuspensaoCalendarioResponse])
def listar_todas_suspensoes(
    db: Session = Depends(get_db),
    usuario_atual = Depends(autorizar(["ADMIN", "COORDENACAO", "SECRETARIA", "DISCENTE"]))
):
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
    dados_atualizacao = dados.model_dump(exclude_unset=True)
    
    registro_atualizado = suspensao.atualizar_suspensao(
        db=db, 
        id_suspensao=id_suspensao, 
        dados_atualizacao=dados_atualizacao
    )
    
    if not registro_atualizado:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Suspensão não encontrada para atualização.")
    
    # Caso 2: Atualização inserindo a data final ou modificando as datas
    if registro_atualizado.data_inicio_suspensao and registro_atualizado.data_fim_suspensao:
        aplicar_suspensao_global(db)
        
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
    
    # Caso 3: Remoção de uma suspensão (recalcula sem ela)
    aplicar_suspensao_global(db)
    
    return None