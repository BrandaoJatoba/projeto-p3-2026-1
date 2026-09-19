from datetime import datetime, timedelta, timezone
import token

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from db.database import get_db
import db.usuario



SECRET_KEY = "chave_secreta_provisoria" # substituir por uma chave secreta segura
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
REFRESH_TOKEN_EXPIRE_DAYS = 7


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

def obter_usuario_atual(
    token: str = Depends(oauth2_scheme),
    db_connection: Session = Depends(get_db)
):
    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado.",
            headers={"WWW-Authenticate": "Bearer"}
        )

    id_usuario = payload.get("id_usuario")

    if id_usuario is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token não contém identificação do usuário.",
            headers={"WWW-Authenticate": "Bearer"}
        )

    usuario = db.usuario.buscar_usuario_por_id(
        db_connection,
        id_usuario
    )

    if usuario is None or usuario.status_conta != "ATIVO":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário não encontrado.",
            headers={"WWW-Authenticate": "Bearer"}
        )

    return usuario

def verificar_permissao(
    usuario,
    perfis_permitidos: list[str],
    db_connection: Session = Depends(get_db)
):
    perfis_usuario = db.usuario.obter_perfis_do_usuario(
        db_connection,
        usuario.id_usuario
    )

    possui_permissao = any(
        perfil in perfis_permitidos
        for perfil in perfis_usuario
    )

    if not possui_permissao:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuário não possui permissão para acessar este recurso."
        )

    return usuario


def autorizar(perfis_permitidos: list[str]):
    def verificar(usuario = Depends(obter_usuario_atual)):
        return verificar_permissao(
            usuario,
            perfis_permitidos
        )

    return verificar


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
