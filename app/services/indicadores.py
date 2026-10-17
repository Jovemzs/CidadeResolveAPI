from datetime import date, datetime, time, timedelta, timezone

from sqlalchemy.orm import Session

from app.core.excecoes import DadosInvalidos
from app.models import StatusOcorrencia, Usuario
from app.repositories.ocorrencia import OcorrenciaRepositorio
from app.schemas.indicadores import IndicadoresSaida, QuantidadePorBairro, QuantidadePorCategoria
from app.services.permissoes import exigir_gestor


class IndicadoresServico:
    def __init__(self, db: Session):
        self.ocorrencias = OcorrenciaRepositorio(db)

    def calcular(
        self, usuario: Usuario, data_inicio: date | None = None, data_fim: date | None = None
    ) -> IndicadoresSaida:
        exigir_gestor(usuario)
        if data_inicio and data_fim and data_inicio > data_fim:
            raise DadosInvalidos("data_inicio não pode ser posterior a data_fim.", "PERIODO_INVALIDO")

        # data_fim é inclusiva: o período vai até o fim daquele dia (UTC).
        inicio = datetime.combine(data_inicio, time.min, timezone.utc) if data_inicio else None
        fim = (
            datetime.combine(data_fim + timedelta(days=1), time.min, timezone.utc)
            if data_fim
            else None
        )

        total = self.ocorrencias.contar(inicio, fim)
        contagem_status = self.ocorrencias.contar_por_status(inicio, fim)
        por_status = {status: contagem_status.get(status, 0) for status in StatusOcorrencia}
        resolvidas = por_status[StatusOcorrencia.RESOLVIDA]
        segundos = self.ocorrencias.tempo_medio_resolucao_segundos(inicio, fim)

        return IndicadoresSaida(
            total_ocorrencias=total,
            por_status=por_status,
            por_categoria=[
                QuantidadePorCategoria(categoria_id=categoria_id, nome=nome, quantidade=quantidade)
                for categoria_id, nome, quantidade in self.ocorrencias.contar_agrupado_por_categoria(
                    inicio, fim
                )
            ],
            por_bairro=[
                QuantidadePorBairro(bairro=bairro, quantidade=quantidade)
                for bairro, quantidade in self.ocorrencias.contar_agrupado_por_bairro(inicio, fim)
            ],
            taxa_resolucao=round(resolvidas / total * 100, 2) if total else 0.0,
            tempo_medio_resolucao_horas=round(segundos / 3600, 2) if segundos is not None else None,
        )
