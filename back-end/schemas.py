from datetime import date
from pydantic import BaseModel, ConfigDict, Field
from typing import Optional


class SemestreCriacao(BaseModel):
    codigo_semestre: str = Field(max_length=6)
    data_inicio_real: date
    data_fim_real: date
    dias_letivos: int

class SemestreAtualizacao(BaseModel):
    data_inicio_real: date
    data_fim_real: date
    dias_letivos: int

class SemestreResposta(BaseModel):

    model_config = ConfigDict(from_attributes=True)

    id_semestre: int
    codigo_semestre: str
    data_inicio_real: Optional[date]
    data_fim_real: Optional[date]
    dias_letivos: Optional[int]