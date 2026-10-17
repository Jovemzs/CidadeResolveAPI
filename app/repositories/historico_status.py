from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models import HistoricoStatus


class HistoricoStatusRepositorio:
    def __init__(self, db: Session):
        self.db = db

    def listar_por_ocorrencia(self, ocorrencia_id: int) -> list[HistoricoStatus]:
        consulta = (
            select(HistoricoStatus)
            .where(HistoricoStatus.ocorrencia_id == ocorrencia_id)
            .options(joinedload(HistoricoStatus.alterado_por))
            .order_by(HistoricoStatus.id)
        )
        return list(self.db.scalars(consulta))

    def adicionar(self, registro: HistoricoStatus) -> HistoricoStatus:
        self.db.add(registro)
        self.db.flush()
        return registro
