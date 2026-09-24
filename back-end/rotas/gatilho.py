from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from schemas import (
    GatilhoAlertaCreate, 
    GatilhoAlertaUpdate, 
    GatilhoAlertaResponse
)
from db.database import get_db
from db import prazo as crud_prazo

# Importações de segurança conforme seu padrão
from security import autorizar, obter_usuario_atual

router = APIRouter(
    prefix="/configuracoes/gatilhos",
    tags=["Configurações - Gatilhos de Alerta"]
)


@router.get("", response_model=List[GatilhoAlertaResponse], status_code=status.HTTP_200_OK)
def listar_gatilhos_por_tipo_prazo(
    id_tipo_prazo: int,
    apenas_ativos: bool = False,
    db_connection: Session = Depends(get_db),
    usuario = Depends(autorizar(["SECRETARIA", "COORDENACAO", "ADMIN"]))
):
    """
    Lista todos os gatilhos configurados para um tipo de prazo específico.
    """
    # Verifica se o tipo de prazo existe
    tipo_prazo = crud_prazo.obter_tipo_prazo_por_id(db_connection, id_tipo_prazo)
    if not tipo_prazo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tipo de prazo com ID {id_tipo_prazo} não encontrado."
        )

    gatilhos = crud_prazo.listar_gatilhos_por_tipo_prazo(
        db_connection=db_connection,
        id_tipo_prazo=id_tipo_prazo,
        apenas_ativos=apenas_ativos
    )
    return gatilhos


@router.get("/{id_gatilho}", response_model=GatilhoAlertaResponse, status_code=status.HTTP_200_OK)
def obter_gatilho_por_id(
    id_gatilho: int,
    db_connection: Session = Depends(get_db),
    usuario = Depends(autorizar(["SECRETARIA", "COORDENACAO", "ADMIN"]))
):
    """
    Busca os detalhes de um gatilho de alerta específico pelo ID.
    """
    gatilho = crud_prazo.obter_gatilho_alerta_por_id(db_connection, id_gatilho)
    if not gatilho:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Gatilho de alerta com ID {id_gatilho} não encontrado."
        )
    return gatilho


@router.post("", response_model=GatilhoAlertaResponse, status_code=status.HTTP_201_CREATED)
def cadastrar_gatilho_alerta(
    dados_gatilho: GatilhoAlertaCreate,
    db_connection: Session = Depends(get_db),
    usuario = Depends(autorizar(["SECRETARIA", "COORDENACAO", "ADMIN"]))
):
    """
    Cadastra um novo gatilho de alerta associado a um tipo de prazo.
    """
    # Valida se o TipoPrazo pai realmente existe
    tipo_prazo = crud_prazo.obter_tipo_prazo_por_id(db_connection, dados_gatilho.id_tipo_prazo)
    if not tipo_prazo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tipo de prazo com ID {dados_gatilho.id_tipo_prazo} não foi encontrado."
        )

    novo_gatilho = crud_prazo.criar_gatilho_alerta(
        db_connection=db_connection,
        id_tipo_prazo=dados_gatilho.id_tipo_prazo,
        dias_antecedencia=dados_gatilho.dias_antecedencia,
        mensagem_template=dados_gatilho.mensagem_template,
        ativo=dados_gatilho.ativo
    )
    return novo_gatilho


@router.put("/{id_gatilho}", response_model=GatilhoAlertaResponse, status_code=status.HTTP_200_OK)
def atualizar_gatilho_alerta(
    id_gatilho: int,
    dados_atualizacao: GatilhoAlertaUpdate,
    db_connection: Session = Depends(get_db),
    usuario = Depends(autorizar(["SECRETARIA", "COORDENACAO", "ADMIN"]))
):
    """
    Atualiza as configurações de um gatilho de alerta existente.
    """
    gatilho_atualizado = crud_prazo.atualizar_gatilho_alerta(
        db_connection=db_connection,
        id_gatilho=id_gatilho,
        dias_antecedencia=dados_atualizacao.dias_antecedencia,
        mensagem_template=dados_atualizacao.mensagem_template,
        ativo=dados_atualizacao.ativo
    )

    if not gatilho_atualizado:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Gatilho de alerta com ID {id_gatilho} não encontrado."
        )

    return gatilho_atualizado


@router.delete("/{id_gatilho}", status_code=status.HTTP_204_NO_CONTENT)
def deletar_gatilho_alerta(
    id_gatilho: int,
    db_connection: Session = Depends(get_db),
    usuario = Depends(autorizar(["ADMIN"]))  # Exclusivo para perfis ADMIN
):
    """
    Remove um gatilho de alerta (Restrito apenas a usuários ADMIN).
    """
    sucesso = crud_prazo.deletar_gatilho_alerta(db_connection=db_connection, id_gatilho=id_gatilho)
    if not sucesso:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Gatilho de alerta com ID {id_gatilho} não encontrado."
        )
    return None