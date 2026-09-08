from datetime import datetime
from typing import List, Optional

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

import models

ph = PasswordHasher()


# --- CRIAR E BUSCAR USUÁRIOS ---

def validar_usuario(db: Session, email: str, senha: str) -> Optional[models.Usuario]:
    """Retorna o usuário se o e-mail existir e a senha estiver correta.
    Retorna None em qualquer outro caso (previne ataques de enumeração de usuários).
    """
    usuario = db.query(models.Usuario).filter(models.Usuario.email == email).first()
    if not usuario:
        return None

    try:
        ph.verify(usuario.senha_hash, senha)
        return usuario
    except VerifyMismatchError:
        return None


def criar_usuario(db: Session, email: str, senha: str) -> Optional[models.Usuario]:
    """Recebe um email e uma senha e cria e salva um usuário no banco de dados.
    Se o email já está salvo no banco de dados, ocorre um erro e nada é salvo.
    """
    senha_transformada = ph.hash(senha)
    novo_usuario = models.Usuario(email=email, senha_hash=senha_transformada)

    try:
        db.add(novo_usuario)
        db.commit()
        db.refresh(novo_usuario)
        return novo_usuario
    except IntegrityError:
        db.rollback()
        return None


def buscar_usuario_por_email(db: Session, email: str) -> Optional[models.Usuario]:
    """
    Retorna um objeto Usuário, com os dados do usuário do email dado.
    """
    return db.query(models.Usuario).filter(models.Usuario.email == email).first()


def buscar_usuario_por_id(db: Session, id_usuario: int) -> Optional[models.Usuario]:
    """
    Retorna um objeto Usuário, com os dados do usuário do id dado.
    """
    return db.query(models.Usuario).filter(models.Usuario.id_usuario == id_usuario).first()


# --- PERFIS & CONTROLE DE ACESSO (RBAC) ---

def obter_perfis_do_usuario(db: Session, id_usuario: int) -> List[int]:
    """Retorna uma lista com os IDs de todos os perfis associados ao usuário."""
    registros = db.query(models.UsuarioPerfil).filter(models.UsuarioPerfil.id_usuario == id_usuario).all()
    return [r.id_perfil for r in registros]


# --- GERENCIAMENTO DE REFRESH TOKENS ---

def buscar_refresh_token(db: Session, token: str) -> Optional[models.SessionRefreshToken]:
    """
    Retorna um objeto refresh_token se ele existir no banco.
    """
    return db.query(models.SessionRefreshToken).filter(
        models.SessionRefreshToken.refresh_token == token
    ).first()


def salvar_refresh_token(
    db: Session, id_usuario: int, token: str, dispositivo: str, data_expiracao: datetime
) -> models.SessionRefreshToken:
    """
    dado os dados do token de acesso, salva esses dados no banco e dados.
    """
    
    novo_token = models.SessionRefreshToken(
        id_usuario=id_usuario,
        refresh_token=token,
        dispositivo_info=dispositivo,
        data_expiracao=data_expiracao,
    )
    db.add(novo_token)
    db.commit()
    db.refresh(novo_token)
    return novo_token


def revogar_refresh_token(db: Session, token: str) -> bool:
    """
    Se o token ainda for válido e estiver salvo no banco de dados, revoga-o e retorna True
    Caso contrário, retorna False.
    """
    session_token = buscar_refresh_token(db, token)

    if session_token:
        session_token.revogado = True
        db.commit()
        return True
    return False