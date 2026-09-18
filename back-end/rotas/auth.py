from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from db.database import get_db
import db.usuario 
import db.tokensessao
import security


router = APIRouter(prefix="/auth", tags=["Autenticação"])


class UsuarioLogin(BaseModel):
    email: EmailStr
    senha: str


class RefreshTokenSchema(BaseModel):
    refresh_token: str


@router.post("/login")
def login(
    dados_login: UsuarioLogin,
    request: Request,
    db_connection: Session = Depends(get_db)
):
    usuario = db.usuario.validar_usuario(
        db_connection,
        email=dados_login.email,
        senha=dados_login.senha
    )

    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-mail ou senha incorretos."
        )

    perfis = db.usuario.obter_perfis_do_usuario(
        db_connection,
        usuario.id_usuario
    )

    dados_token = {
        "sub": usuario.email,
        "id_usuario": usuario.id_usuario,
        "perfis": perfis
    }

    access_token = security.criar_token_acesso(dados_token)
    refresh_token, data_expiracao = security.criar_refresh_token(dados_token)

    dispositivo = request.headers.get(
        "User-Agent",
        "Desconhecido"
    )

    db.tokensessao.salvar_refresh_token(
        db_connection,
        id_usuario=usuario.id_usuario,
        token=refresh_token,
        dispositivo=dispositivo,
        data_expiracao=data_expiracao
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "usuario": {
            "id_usuario": usuario.id_usuario,
            "email": usuario.email,
            "perfis": perfis
        }
    }