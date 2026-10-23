from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.models import Categoria, Ocorrencia, StatusOcorrencia


class OcorrenciaRepositorio:
    def __init__(self, db: Session):
        self.db = db

    def obter(self, ocorrencia_id: int) -> Ocorrencia | None:
        consulta = (
            select(Ocorrencia)
            .where(Ocorrencia.id == ocorrencia_id)
            .options(
                joinedload(Ocorrencia.categoria),
                joinedload(Ocorrencia.autor),
                selectinload(Ocorrencia.fotos),
            )
        )
        return self.db.scalar(consulta)

    def travar(self, ocorrencia_id: int) -> None:
        """Trava a linha até o fim da transação, para mudanças simultâneas esperarem a vez."""
        self.db.execute(select(Ocorrencia.id).where(Ocorrencia.id == ocorrencia_id).with_for_update())

    def listar(
        self,
        *,
        bairro: str | None = None,
        categoria_id: int | None = None,
        status: StatusOcorrencia | None = None,
        autor_id: int | None = None,
        pagina: int = 1,
        tamanho: int = 20,
    ) -> tuple[list[Ocorrencia], int]:
        filtros = []
        if bairro:
            filtros.append(func.lower(Ocorrencia.bairro) == bairro.strip().lower())
        if categoria_id is not None:
            filtros.append(Ocorrencia.categoria_id == categoria_id)
        if status is not None:
            filtros.append(Ocorrencia.status == status)
        if autor_id is not None:
            filtros.append(Ocorrencia.autor_id == autor_id)

        total = self.db.scalar(select(func.count(Ocorrencia.id)).where(*filtros)) or 0
        consulta = (
            select(Ocorrencia)
            .where(*filtros)
            .options(joinedload(Ocorrencia.categoria), joinedload(Ocorrencia.autor))
            .order_by(Ocorrencia.criado_em.desc(), Ocorrencia.id.desc())
            .offset((pagina - 1) * tamanho)
            .limit(tamanho)
        )
        return list(self.db.scalars(consulta)), total

    def adicionar(self, ocorrencia: Ocorrencia) -> Ocorrencia:
        self.db.add(ocorrencia)
        self.db.flush()
        return ocorrencia

    def excluir(self, ocorrencia: Ocorrencia) -> None:
        self.db.delete(ocorrencia)
        self.db.flush()

    def contar_por_categoria(self, categoria_id: int) -> int:
        return (
            self.db.scalar(
                select(func.count(Ocorrencia.id)).where(Ocorrencia.categoria_id == categoria_id)
            )
            or 0
        )

    # Consultas dos indicadores. O período filtra pela data de criação.

    @staticmethod
    def _filtros_periodo(inicio: datetime | None, fim: datetime | None) -> list:
        filtros = []
        if inicio is not None:
            filtros.append(Ocorrencia.criado_em >= inicio)
        if fim is not None:
            filtros.append(Ocorrencia.criado_em < fim)
        return filtros

    def contar(self, inicio: datetime | None, fim: datetime | None) -> int:
        consulta = select(func.count(Ocorrencia.id)).where(*self._filtros_periodo(inicio, fim))
        return self.db.scalar(consulta) or 0

    def contar_por_status(
        self, inicio: datetime | None, fim: datetime | None
    ) -> dict[StatusOcorrencia, int]:
        consulta = (
            select(Ocorrencia.status, func.count(Ocorrencia.id))
            .where(*self._filtros_periodo(inicio, fim))
            .group_by(Ocorrencia.status)
        )
        return {status: quantidade for status, quantidade in self.db.execute(consulta)}

    def contar_agrupado_por_categoria(
        self, inicio: datetime | None, fim: datetime | None
    ) -> list[tuple[int, str, int]]:
        quantidade = func.count(Ocorrencia.id)
        consulta = (
            select(Categoria.id, Categoria.nome, quantidade)
            .join(Categoria, Categoria.id == Ocorrencia.categoria_id)
            .where(*self._filtros_periodo(inicio, fim))
            .group_by(Categoria.id, Categoria.nome)
            .order_by(quantidade.desc(), Categoria.nome)
        )
        return [tuple(linha) for linha in self.db.execute(consulta)]

    def contar_agrupado_por_bairro(
        self, inicio: datetime | None, fim: datetime | None
    ) -> list[tuple[str, int]]:
        quantidade = func.count(Ocorrencia.id)
        consulta = (
            select(Ocorrencia.bairro, quantidade)
            .where(*self._filtros_periodo(inicio, fim))
            .group_by(Ocorrencia.bairro)
            .order_by(quantidade.desc(), Ocorrencia.bairro)
        )
        return [tuple(linha) for linha in self.db.execute(consulta)]

    def tempo_medio_resolucao_segundos(
        self, inicio: datetime | None, fim: datetime | None
    ) -> float | None:
        duracao = func.extract("epoch", Ocorrencia.resolvido_em - Ocorrencia.criado_em)
        consulta = select(func.avg(duracao)).where(
            Ocorrencia.status == StatusOcorrencia.RESOLVIDA,
            Ocorrencia.resolvido_em.is_not(None),
            *self._filtros_periodo(inicio, fim),
        )
        media = self.db.scalar(consulta)
        return float(media) if media is not None else None
