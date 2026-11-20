"""
Rotas do Gerador de Alertas.

- GET /alertas/pendentes: roda o motor de varredura e lista os alertas a enviar.
  Só consulta: não envia e-mail nem grava histórico.

  - POST /alertas/minutas/preview: monta o e-mail de cada alerta selecionado para
  a Secretaria revisar. Também não envia nem grava nada.
"""

from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from db.database import get_db
from schemas import AlertaPendenteResponse, MinutaPreviewRequest, MinutaPreviewResponse
from services import alerta_scanner_service, minuta_service
from security import autorizar

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
    Gera as minutas dos alertas selecionados.

    Só gera minuta para pares (aluno, gatilho) que estão pendentes de verdade
    (assim o anti-spam do motor é respeitado). Os demais voltam em "ignorados".
    """
    pendentes = alerta_scanner_service.listar_alertas_pendentes(db_connection, hoje=data_referencia)
    por_par = {(a["id_estudante"], a["id_gatilho"]): a for a in pendentes}

    minutas = []
    ignorados = []
    vistos = set()

    for item in dados.itens:
        par = (item.id_estudante, item.id_gatilho)
        if par in vistos:
            continue  # item repetido na requisição
        vistos.add(par)

        alerta = por_par.get(par)
        if alerta is None:
            ignorados.append({
                "id_estudante": item.id_estudante,
                "id_gatilho": item.id_gatilho,
                "motivo": "Alerta não está pendente (já enviado, fora da janela do gatilho ou inexistente).",
            })
            continue

        minutas.append(minuta_service.gerar_minuta(alerta))

    return {"minutas": minutas, "ignorados": ignorados}