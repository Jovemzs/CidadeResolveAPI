from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, agora


class Foto(Base):
    __tablename__ = "foto"

    id: Mapped[int] = mapped_column(primary_key=True)
    ocorrencia_id: Mapped[int] = mapped_column(
        ForeignKey("ocorrencia.id", ondelete="CASCADE"), index=True
    )
    nome_arquivo: Mapped[str] = mapped_column(String(255))
    tipo_conteudo: Mapped[str] = mapped_column(String(50))
    tamanho_bytes: Mapped[int] = mapped_column(Integer)
    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=agora, server_default=func.now()
    )

    ocorrencia: Mapped["Ocorrencia"] = relationship(back_populates="fotos")
