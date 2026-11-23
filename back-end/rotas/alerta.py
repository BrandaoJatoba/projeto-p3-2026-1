"""
Rotas do Gerador de Alertas.

- GET /alertas/pendentes: roda o motor de varredura e lista os alertas a enviar.
  Só consulta: não envia e-mail nem grava histórico.
- POST /alertas/minutas/preview: monta o e-mail de cada alerta selecionado para
  a Secretaria revisar. Também não envia nem grava nada.
- POST /alertas/disparar/individual: envia um alerta revisado e grava o histórico.
- POST /alertas/disparar/lote: aceita o lote, responde 202 e envia em background;
  cada item gera seu próprio registro (ENVIADO ou FALHA).
"""

from datetime import date
from typing import List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from db.database import get_db
from schemas import (
    AlertaPendenteResponse,
    DisparoIndividualRequest,
    DisparoLoteRequest,
    DisparoLoteResponse,
    HistoricoAlertaEnviadoResponse,
    MinutaPreviewRequest,
    MinutaPreviewResponse,
)
from security import autorizar
from services import alerta_disparo_service, alerta_scanner_service, minuta_service
from services.alerta_disparo_service import (
    ConflitoDisparo,
    DisparoInvalido,
    RecursoNaoEncontrado,
)

PERFIS_GESTAO = ["SECRETARIA", "COORDENACAO", "ADMIN"]

router = APIRouter(prefix="/alertas", tags=["Alertas"])


@router.get("/pendentes", response_model=List[AlertaPendenteResponse])
def listar_alertas_pendentes(
    data_referencia: Optional[date] = Query(
        None, description="Simula a varredura em outra data (padrão: hoje)."
    ),
    db_connection: Session = Depends(get_db),
    usuario=Depends(autorizar(PERFIS_GESTAO)),
):
    """Lista os alertas pendentes, do mais urgente para o menos urgente."""
    return alerta_scanner_service.listar_alertas_pendentes(
        db_connection, hoje=data_referencia
    )


@router.post("/minutas/preview", response_model=MinutaPreviewResponse)
def gerar_preview_minutas(
    dados: MinutaPreviewRequest,
    data_referencia: Optional[date] = Query(
        None, description="Mesma data usada no GET /alertas/pendentes (padrão: hoje)."
    ),
    db_connection: Session = Depends(get_db),
    usuario=Depends(autorizar(PERFIS_GESTAO)),
):
    """
    Gera as minutas dos alertas selecionados para a Secretaria revisar.

    Só pares pendentes de verdade viram minuta (anti-spam do motor); os demais
    voltam em "ignorados". A regra fica em minuta_service.gerar_minutas_selecionadas.
    """
    pares = [(item.id_estudante, item.id_gatilho) for item in dados.itens]
    return minuta_service.gerar_minutas_selecionadas(
        db_connection, pares, dados.template_customizado, hoje=data_referencia
    )


@router.post(
    "/disparar/individual",
    response_model=HistoricoAlertaEnviadoResponse,
    status_code=status.HTTP_201_CREATED,
)
def disparar_alerta_individual(
    dados: DisparoIndividualRequest,
    db_connection: Session = Depends(get_db),
    usuario=Depends(autorizar(PERFIS_GESTAO)),
):
    """Envia um alerta revisado e devolve o registro criado no histórico."""
    try:
        return alerta_disparo_service.disparar_individual(
            db_connection,
            id_estudante=dados.id_estudante,
            id_gatilho=dados.id_gatilho,
            assunto=dados.assunto,
            corpo_mensagem=dados.corpo_mensagem,
            email_destino=dados.email_destino,
            cc_adicionais=dados.cc_adicionais,
            ignorar_cc_ids=dados.ignorar_cc_ids,
        )
    except RecursoNaoEncontrado as erro:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(erro))
    except ConflitoDisparo as erro:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(erro))
    except DisparoInvalido as erro:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(erro)
        )


@router.post(
    "/disparar/lote",
    response_model=DisparoLoteResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def disparar_alertas_em_lote(
    dados: DisparoLoteRequest,
    background_tasks: BackgroundTasks,
    db_connection: Session = Depends(get_db),
    usuario=Depends(autorizar(PERFIS_GESTAO)),
):
    """Valida o lote e agenda o envio em background."""
    itens = [item.model_dump() for item in dados.itens]
    aceitos, recusados = alerta_disparo_service.validar_itens_lote(
        db_connection, itens
    )

    if aceitos:
        background_tasks.add_task(
            alerta_disparo_service.processar_lote,
            aceitos,
            dados.template_global_override,
        )

    return {
        "status": "PROCESSANDO",
        "itens_aceitos": len(aceitos),
        "recusados": recusados,
    }
