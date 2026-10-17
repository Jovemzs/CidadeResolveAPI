from datetime import datetime

from sqlalchemy import DateTime, Enum, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, agora
from app.models.enums import Papel


class Usuario(Base):
    __tablename__ = "usuario"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(255), unique=True)
    senha_hash: Mapped[str] = mapped_column(Text)
    papel: Mapped[Papel] = mapped_column(
        Enum(Papel, name="papel"), default=Papel.CIDADAO, server_default=Papel.CIDADAO.value
    )
    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=agora, server_default=func.now()
    )

    @property
    def eh_gestor(self) -> bool:
        return self.papel == Papel.GESTOR
