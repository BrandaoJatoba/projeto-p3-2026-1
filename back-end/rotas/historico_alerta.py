"""
Rotas do Histórico de Alertas Enviados (auditoria).

- GET /historico-alertas: lista paginada com filtros, enriquecida com nome do
  discente, matrícula e nome do prazo. Só consulta.
- POST /historico-alertas/{id}/reenviar: reprocessa um envio com status FALHA,
  usando o mesmo destinatário e a mesma lista de CC gravados no registro.
"""

from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from db import alerta as crud_alerta
from db.database import get_db
from db.enumStatus import StatusEnvioAlerta
from schemas import (
    HistoricoAlertaDetalhado,
    HistoricoAlertaDetalhadoPaginado,
    HistoricoAlertaEnviadoResponse,
)
from security import autorizar
from services import alerta_disparo_service
from services.alerta_disparo_service import ConflitoDisparo, RecursoNaoEncontrado

PERFIS_GESTAO = ["SECRETARIA", "COORDENACAO", "ADMIN"]

router = APIRouter(prefix="/historico-alertas", tags=["Histórico de Alertas"])


@router.get("", response_model=HistoricoAlertaDetalhadoPaginado)
def listar_historico_alertas(
    id_estudante: Optional[int] = Query(None, gt=0),
    id_gatilho: Optional[int] = Query(None, gt=0),
    status_envio: Optional[StatusEnvioAlerta] = Query(None),
    data_inicio: Optional[date] = Query(None, description="Envios a partir deste dia (inclusive)."),
    data_fim: Optional[date] = Query(None, description="Envios até este dia (inclusive)."),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db_connection: Session = Depends(get_db),
    usuario=Depends(autorizar(PERFIS_GESTAO)),
):
    """Lista o histórico de alertas, do envio mais recente para o mais antigo."""
    if data_inicio and data_fim and data_inicio > data_fim:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="data_inicio não pode ser posterior a data_fim.",
        )

    total, linhas = crud_alerta.listar_historico_alertas_filtrados(
        db_connection,
        id_estudante=id_estudante,
        id_gatilho=id_gatilho,
        status_envio=status_envio,
        data_inicio=data_inicio,
        data_fim=data_fim,
        skip=skip,
        limit=limit,
    )

    itens = [
        HistoricoAlertaDetalhado(
            **HistoricoAlertaEnviadoResponse.model_validate(registro).model_dump(),
            nome_discente=nome_discente,
            matricula=matricula,
            nome_prazo=nome_prazo,
        )
        for registro, nome_discente, matricula, nome_prazo in linhas
    ]
    return {"total": total, "skip": skip, "limit": limit, "itens": itens}


@router.post("/{id_historico_alerta}/reenviar", response_model=HistoricoAlertaEnviadoResponse)
def reenviar_alerta(
    id_historico_alerta: int,
    db_connection: Session = Depends(get_db),
    usuario=Depends(autorizar(PERFIS_GESTAO)),
):
    """
    Reenvia um alerta que falhou. Atualiza o próprio registro (status e data).
    Se falhar de novo, o registro continua FALHA e pode ser reenviado depois.
    """
    try:
        return alerta_disparo_service.reenviar(db_connection, id_historico_alerta)
    except RecursoNaoEncontrado as erro:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(erro))
    except ConflitoDisparo as erro:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(erro))
