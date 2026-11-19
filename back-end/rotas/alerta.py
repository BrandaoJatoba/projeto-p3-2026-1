"""
Rotas do Gerador de Alertas.

- GET /alertas/pendentes: roda o motor de varredura e lista os alertas a enviar.
  Só consulta: não envia e-mail nem grava histórico.
"""

from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from db.database import get_db
from schemas import AlertaPendenteResponse
from security import autorizar
from services import alerta_scanner_service

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
    return alerta_scanner_service.listar_alertas_pendentes(db_connection, hoje=data_referencia)