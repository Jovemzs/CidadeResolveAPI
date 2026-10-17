from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

from app.models import StatusOcorrencia


class OcorrenciaEntrada(BaseModel):
    titulo: Annotated[str, StringConstraints(strip_whitespace=True, min_length=5, max_length=120)]
    descricao: Annotated[str, StringConstraints(strip_whitespace=True, min_length=10)]
    categoria_id: int
    endereco: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=255)]
    bairro: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=80)]
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)

    @model_validator(mode="after")
    def coordenadas_juntas(self):
        if (self.latitude is None) != (self.longitude is None):
            raise ValueError("Latitude e longitude devem ser informadas juntas.")
        return self


class StatusEntrada(BaseModel):
    status: StatusOcorrencia
    comentario: Annotated[str, StringConstraints(strip_whitespace=True, max_length=500)] | None = None


class AutorSaida(BaseModel):
    """Dados públicos do autor: apenas o nome, nunca o e-mail."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str


class CategoriaResumo(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str


class FotoSaida(BaseModel):
    id: int
    url: str
    tipo_conteudo: str
    tamanho_bytes: int
    criado_em: datetime


class OcorrenciaSaida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    titulo: str
    descricao: str
    status: StatusOcorrencia
    categoria: CategoriaResumo
    autor: AutorSaida
    endereco: str
    bairro: str
    latitude: float | None
    longitude: float | None
    criado_em: datetime
    atualizado_em: datetime
    resolvido_em: datetime | None


class OcorrenciaDetalhe(OcorrenciaSaida):
    fotos: list[FotoSaida]


class PaginaOcorrencias(BaseModel):
    itens: list[OcorrenciaSaida]
    total: int
    pagina: int
    tamanho: int


class HistoricoSaida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    status_anterior: StatusOcorrencia | None
    status_novo: StatusOcorrencia
    comentario: str | None
    alterado_por: AutorSaida
    criado_em: datetime
