from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

# Importe os schemas, conexão com o banco e dependência de autenticação do seu projeto
from schemas import TipoPrazoCreate, TipoPrazoUpdate, TipoPrazoResponse
from db.database import get_db  # Função/Gerador de sessão do SQLAlchemy
from security import autorizar, obter_usuario_atual

from db import prazo as crud_prazo

router = APIRouter(
    prefix="/configuracoes/prazos",
    tags=["Configurações - Prazos"]
)


@router.get("", response_model=List[TipoPrazoResponse], status_code=status.HTTP_200_OK)
def listar_prazos(
    pular: int = 0,
    limite: int = 100,
    db_connection: Session = Depends(get_db),
    usuario=Depends(autorizar(["SECRETARIA", "COORDENACAO", "ADMIN"]))
):
    """
    Lista todos os tipos de prazos cadastrados com suporte a paginação.
    """
    prazos = crud_prazo.listar_tipos_prazos(db_connection=db_connection, pular=pular, limite=limite)
    return prazos


@router.post("", response_model=TipoPrazoResponse, status_code=status.HTTP_201_CREATED)
def cadastrar_tipo_prazo(
    dados_prazo: TipoPrazoCreate,
    db_connection: Session = Depends(get_db),
    usuario=Depends(autorizar(["SECRETARIA", "COORDENACAO", "ADMIN"]))
):
    """
    Cadastra um novo tipo de prazo.
    """
    # Verifica se já existe um prazo com o mesmo código único
    prazo_existente = crud_prazo.obter_tipo_prazo_por_codigo(
        db_connection=db_connection, 
        codigo_prazo=dados_prazo.codigo_prazo
    )
    if prazo_existente:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Já existe um tipo de prazo cadastrado com o código '{dados_prazo.codigo_prazo}'."
        )

    novo_prazo = crud_prazo.criar_tipo_prazo(
        db_connection=db_connection,
        codigo_prazo=dados_prazo.codigo_prazo,
        nome_prazo=dados_prazo.nome_prazo,
        descricao=dados_prazo.descricao
    )
    return novo_prazo


@router.put("/{id_prazo}", response_model=TipoPrazoResponse, status_code=status.HTTP_200_OK)
def atualizar_tipo_prazo(
    id_prazo: int,
    dados_atualizacao: TipoPrazoUpdate,
    db_connection: Session = Depends(get_db),
    usuario=Depends(autorizar(["SECRETARIA", "COORDENACAO", "ADMIN"]))
):
    """
    Atualiza um tipo de prazo existente pelo ID.
    """
    # Se o código do prazo for informado para alteração, verifica se não conflita com outro existente
    if dados_atualizacao.codigo_prazo:
        prazo_existente = crud_prazo.obter_tipo_prazo_por_codigo(
            db_connection=db_connection, 
            codigo_prazo=dados_atualizacao.codigo_prazo
        )
        if prazo_existente and prazo_existente.id_tipo_prazo != id_prazo:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"O código '{dados_atualizacao.codigo_prazo}' já está em uso por outro tipo de prazo."
            )

    prazo_atualizado = crud_prazo.atualizar_tipo_prazo(
        db_connection=db_connection,
        id_tipo_prazo=id_prazo,
        codigo_prazo=dados_atualizacao.codigo_prazo,
        nome_prazo=dados_atualizacao.nome_prazo,
        descricao=dados_atualizacao.descricao
    )

    if not prazo_atualizado:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tipo de prazo com ID {id_prazo} não foi encontrado."
        )

    return prazo_atualizado


@router.delete("/{id_prazo}", status_code=status.HTTP_204_NO_CONTENT)
def deletar_tipo_prazo(
    id_prazo: int,
    db_connection: Session = Depends(get_db),
    usuario=Depends(autorizar(["ADMIN"]))  # Rota protegida apenas para perfil ADMIN
):
    """
    Deleta um tipo de prazo existente pelo ID (Requer permissão de Administrador).
    """
    sucesso = crud_prazo.deletar_tipo_prazo(db_connection=db_connection, id_tipo_prazo=id_prazo)
    if not sucesso:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tipo de prazo com ID {id_prazo} não foi encontrado."
        )
    return None

@router.get("/{id_prazo}", response_model=TipoPrazoResponse, status_code=status.HTTP_200_OK)
def obter_prazo_por_id(
    id_prazo: int,
    db_connection: Session = Depends(get_db),
    usuario = Depends(autorizar(["SECRETARIA", "COORDENACAO", "ADMIN"]))
):
    """
    Busca os detalhes de um prazo de alerta específico pelo ID.
    """
    prazo = crud_prazo.obter_tipo_prazo_por_id(db_connection, id_prazo)
    if not prazo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Gatilho de alerta com ID {id_prazo} não encontrado."
        )
    return prazo
