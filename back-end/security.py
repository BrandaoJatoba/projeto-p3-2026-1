from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from db.database import get_db



SECRET_KEY = "chave_secreta_provisoria" # substituir por uma chave secreta segura em produção
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
REFRESH_TOKEN_EXPIRE_DAYS = 7


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

def criar_token_acesso(data: dict) -> str:
    """Gera o Access Token JWT válido por 60 minutos."""

    to_encode = data.copy()

    expiracao = datetime.now(timezone.utc) + timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )

    to_encode.update({"exp": expiracao})

    token = jwt.encode(
        to_encode,
        SECRET_KEY,
        algorithm=ALGORITHM
    )

    if isinstance(token, bytes):
        return token.decode("utf-8")

    return token


def criar_refresh_token(data: dict) -> tuple[str, datetime]:
    """Gera o Refresh Token válido por 7 dias e retorna a data exata de expiração."""

    to_encode = data.copy()

    data_expiracao = datetime.now(timezone.utc) + timedelta(
        days=REFRESH_TOKEN_EXPIRE_DAYS
    )

    to_encode.update({
        "exp": data_expiracao,
        "type": "refresh"
    })

    token = jwt.encode(
        to_encode,
        SECRET_KEY,
        algorithm=ALGORITHM
    )

    if isinstance(token, bytes):
        token = token.decode("utf-8")

    return token, data_expiracao