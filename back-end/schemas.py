from datetime import date
from pydantic import BaseModel


class SemestreCriacao(BaseModel):
    codigo_semestre: str
    data_inicio_real: date
    data_fim_real: date
    dias_letivos: int

class SemestreAtualizacao(BaseModel):
    data_inicio_real: date
    data_fim_real: date
    dias_letivos: int

class SemestreResposta(BaseModel):
    id_semestre: int
    codigo_semestre: str
    data_inicio_real: date
    data_fim_real: date
    dias_letivos: int