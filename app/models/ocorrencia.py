from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Enum, ForeignKey, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, agora
from app.models.categoria import Categoria
from app.models.enums import StatusOcorrencia
from app.models.usuario import Usuario


class Ocorrencia(Base):
    __tablename__ = "ocorrencia"

    id: Mapped[int] = mapped_column(primary_key=True)
    titulo: Mapped[str] = mapped_column(String(120))
    descricao: Mapped[str] = mapped_column(Text)
    categoria_id: Mapped[int] = mapped_column(ForeignKey("categoria.id", ondelete="RESTRICT"))
    autor_id: Mapped[int] = mapped_column(ForeignKey("usuario.id", ondelete="RESTRICT"))
    status: Mapped[StatusOcorrencia] = mapped_column(
        Enum(StatusOcorrencia, name="status_ocorrencia"),
        default=StatusOcorrencia.ABERTA,
        server_default=StatusOcorrencia.ABERTA.value,
    )
    endereco: Mapped[str] = mapped_column(String(255))
    bairro: Mapped[str] = mapped_column(String(80), index=True)
    latitude: Mapped[Decimal | None] = mapped_column(Numeric(9, 6))
    longitude: Mapped[Decimal | None] = mapped_column(Numeric(9, 6))
    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=agora, server_default=func.now()
    )
    atualizado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=agora, onupdate=agora, server_default=func.now()
    )
    resolvido_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    categoria: Mapped[Categoria] = relationship()
    autor: Mapped[Usuario] = relationship()
    fotos: Mapped[list["Foto"]] = relationship(
        back_populates="ocorrencia",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="Foto.id",
    )
    historico: Mapped[list["HistoricoStatus"]] = relationship(
        back_populates="ocorrencia",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="HistoricoStatus.id",
    )
