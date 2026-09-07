from sqlalchemy.orm import Session
import models
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from sqlalchemy.exc import IntegrityError

ph = PasswordHasher()

def validar_usuario(db: Session, email: str, senha: str):
    usuario = db.query(models.Usuario).filter(models.Usuario.email == email).first()
    try:
        if(usuario == None):
            raise ValueError("User not found.") 
        ph.verify(usuario.senha_hash, senha)
        return usuario    #Senha confere
    except ValueError:
        return None   #usuário não encontrado
    except VerifyMismatchError:
        return False    #senha errada

def criar_usuario(db: Session, email: str, senha: str):
    senha_transformada = ph.hash(senha)
    novo_usuario = models.Usuario(email=email, senha_hash=senha_transformada)
    
    try:
        db.add(novo_usuario)
        db.commit()
        db.refresh(novo_usuario)
        return novo_usuario
    except IntegrityError:
        db.rollback()  # Cancela a transação pendente
        return None    # Indica que o e-mail já está cadastrado