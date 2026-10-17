from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.core.dependencias import UsuarioAtual, obter_indicadores_servico
from app.schemas.indicadores import IndicadoresSaida
from app.services.indicadores import IndicadoresServico

router = APIRouter(prefix="/indicadores", tags=["Indicadores"])


@router.get("", response_model=IndicadoresSaida, summary="Indicadores de atendimento (gestor)")
def indicadores(
    usuario: UsuarioAtual,
    servico: Annotated[IndicadoresServico, Depends(obter_indicadores_servico)],
    data_inicio: Annotated[date | None, Query(description="Criadas a partir desta data")] = None,
    data_fim: Annotated[date | None, Query(description="Criadas até esta data (inclusive)")] = None,
):
    return servico.calcular(usuario, data_inicio, data_fim)
