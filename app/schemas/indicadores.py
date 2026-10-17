from pydantic import BaseModel

from app.models import StatusOcorrencia


class QuantidadePorCategoria(BaseModel):
    categoria_id: int
    nome: str
    quantidade: int


class QuantidadePorBairro(BaseModel):
    bairro: str
    quantidade: int


class IndicadoresSaida(BaseModel):
    total_ocorrencias: int
    por_status: dict[StatusOcorrencia, int]
    por_categoria: list[QuantidadePorCategoria]
    por_bairro: list[QuantidadePorBairro]
    taxa_resolucao: float
    tempo_medio_resolucao_horas: float | None
