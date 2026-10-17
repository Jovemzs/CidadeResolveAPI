from datetime import datetime, timezone

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


def agora() -> datetime:
    return datetime.now(timezone.utc)
