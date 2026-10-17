from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.models import Foto


class FotoRepositorio:
    def __init__(self, db: Session):
        self.db = db

    def obter(self, foto_id: int) -> Foto | None:
        consulta = select(Foto).where(Foto.id == foto_id).options(joinedload(Foto.ocorrencia))
        return self.db.scalar(consulta)

    def contar_por_ocorrencia(self, ocorrencia_id: int) -> int:
        consulta = select(func.count(Foto.id)).where(Foto.ocorrencia_id == ocorrencia_id)
        return self.db.scalar(consulta) or 0

    def adicionar(self, foto: Foto) -> Foto:
        self.db.add(foto)
        self.db.flush()
        return foto

    def excluir(self, foto: Foto) -> None:
        self.db.delete(foto)
        self.db.flush()
