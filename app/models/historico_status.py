from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, agora
from app.models.enums import StatusOcorrencia
from app.models.usuario import Usuario


class HistoricoStatus(Base):
    __tablename__ = "historico_status"

    id: Mapped[int] = mapped_column(primary_key=True)
    ocorrencia_id: Mapped[int] = mapped_column(
        ForeignKey("ocorrencia.id", ondelete="CASCADE"), index=True
    )
    status_anterior: Mapped[StatusOcorrencia | None] = mapped_column(
        Enum(StatusOcorrencia, name="status_ocorrencia")
    )
    status_novo: Mapped[StatusOcorrencia] = mapped_column(
        Enum(StatusOcorrencia, name="status_ocorrencia")
    )
    alterado_por_id: Mapped[int] = mapped_column(ForeignKey("usuario.id", ondelete="RESTRICT"))
    comentario: Mapped[str | None] = mapped_column(String(500))
    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=agora, server_default=func.now()
    )

    ocorrencia: Mapped["Ocorrencia"] = relationship(back_populates="historico")
    alterado_por: Mapped[Usuario] = relationship()
