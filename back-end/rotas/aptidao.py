from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session
from db.database import get_db  # Importa a tua função que fornece a sessão da BD
from db.models import Estudante # Importa o modelo do estudante para validação
from services import calcular_aptidao_defesa # O service que acabaste de criar
from schemas import StatusDefesaResponse

router = APIRouter(prefix="/aptidao", tags=["Aptidão para Defesa"])

@router.get("/estudante/{id_estudante}", response_model=StatusDefesaResponse)
def verificar_aptidao_defesa(
    id_estudante: int, 
    db: Session = Depends(get_db)
):
    # 1. Verifica se o estudante existe (opcional, mas recomendado)
    estudante = db.query(Estudante).filter(Estudante.id_estudante == id_estudante).first()
    if not estudante:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Estudante não encontrado."
        )

    # 2. Chama o serviço passando a sessão da base de dados e o ID
    resultado_aptidao = calcular_aptidao_defesa(db=db, id_estudante=id_estudante)

    # 3. Retorna o resultado (o FastAPI converte automaticamente para o schema)
    return resultado_aptidao