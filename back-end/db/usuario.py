from typing import Optional

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

import models

ph = PasswordHasher()


# --- CRIAR E BUSCAR USUÁRIOS ---

def validar_usuario(db: Session, email: str, senha: str) -> Optional[models.Usuario]:
    """
    Retorna o usuário se o e-mail existir e a senha estiver correta.
    Retorna None em qualquer outro caso (previne ataques de enumeração de usuários).
    """
    usuario = db.query(models.Usuario).filter(models.Usuario.email == email, models.Usuario.status_conta == "ATIVO").first()
    if not usuario:
        return None

    try:
        ph.verify(usuario.senha_hash, senha)
        return usuario
    except VerifyMismatchError:
        return None

def criar_usuario(db: Session, email: str, senha: str) -> Optional[models.Usuario]:
    """
    Recebe um email e uma senha e cria e salva um usuário no banco de dados. Se o email já está salvo no banco de dados, ocorre um erro e nada é salvo.
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

# -- PERFIS -- #

def obter_perfis_do_usuario(db: Session, id_usuario: int) -> List[int]:
    """
    Retorna uma lista com os IDs de todos os perfis associados ao usuário.
    """
    registros = db.query(models.UsuarioPerfil).filter(models.UsuarioPerfil.id_usuario == id_usuario).all()
    return [r.id_perfil for r in registros]