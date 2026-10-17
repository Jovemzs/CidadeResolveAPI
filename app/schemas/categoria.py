from typing import Annotated

from pydantic import BaseModel, ConfigDict, StringConstraints


class CategoriaEntrada(BaseModel):
    nome: Annotated[str, StringConstraints(strip_whitespace=True, min_length=2, max_length=80)]
    descricao: Annotated[str, StringConstraints(strip_whitespace=True, max_length=255)] | None = None
    ativa: bool = True


class CategoriaSaida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    descricao: str | None
    ativa: bool
