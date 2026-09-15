from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

import models


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
    Recebe os dados do token de acesso, salva esses dados no banco e dados.
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