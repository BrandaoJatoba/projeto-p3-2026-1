from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from db.database import get_db
# importe sua função e o schema OAuth2 adequado
from db.tokensessao import revogar_refresh_token
import security
from pydantic import BaseModel

router = APIRouter(tags=["Log Out"])

class LogoutRequest(BaseModel):
    refresh_token: str

# Adicione esta rota logo abaixo da sua rota de @router.post("/login") no arquivo auth.py

@router.post("/logout")
def logout(
    dados_logout: LogoutRequest, # Recebe o refresh_token via JSON no corpo da requisição
    usuario = Depends(security.obter_usuario_atual), # Exige o Access Token no cabeçalho (Authorization: Bearer ...)
    db_connection: Session = Depends(get_db)
):
    """
    Rota para encerrar a sessão do usuário.
    O frontend deve enviar o Refresh Token no corpo da requisição e o Access Token no Header.
    """
    
    # Chama a função que você mencionou ter no módulo de banco de dados
    # Assumindo que ela está no módulo db.tokensessao
    sucesso = revogar_refresh_token(
        db_connection,
        token=dados_logout.refresh_token
    )

    if not sucesso:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Refresh token inválido, não encontrado ou já revogado."
        )

    return {"message": "Logout realizado com sucesso."}