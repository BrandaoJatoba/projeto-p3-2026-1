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

# Schema Base com os campos comuns
class SuspensaoCalendarioBase(BaseModel):
    motivo: Optional[str] = Field(None, max_length=100, description="Motivo da suspensão (ex: Greve, Pandemia)")
    data_inicio_suspensao: date = Field(..., description="Data de início da suspensão")
    data_fim_suspensao: Optional[date] = Field(None, description="Data de término da suspensão")
    dias_suspensos: Optional[int] = Field(None, description="Quantidade de dias letivos suspensos")

# Schema para criação (POST) - Exige o id_semestre
class SuspensaoCalendarioCreate(SuspensaoCalendarioBase):
    id_semestre: int = Field(..., description="ID do semestre letivo associado")

# Schema para atualização (PUT/PATCH) - Torna todos os campos opcionais
class SuspensaoCalendarioUpdate(BaseModel):
    id_semestre: Optional[int] = None
    motivo: Optional[str] = Field(None, max_length=100)
    data_inicio_suspensao: Optional[date] = None
    data_fim_suspensao: Optional[date] = None
    dias_suspensos: Optional[int] = None

# Schema de resposta (GET ou retorno de POST/PUT) - Inclui o ID gerado pelo banco
class SuspensaoCalendarioResponse(SuspensaoCalendarioBase):
    id_suspensao: int
    id_semestre: int

    # Configuração necessária para o Pydantic ler objetos do SQLAlchemy
    model_config = ConfigDict(from_attributes=True)