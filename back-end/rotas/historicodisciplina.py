from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

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
