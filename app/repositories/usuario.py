from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Usuario


class UsuarioRepositorio:
    def __init__(self, db: Session):
        self.db = db

    def obter(self, usuario_id: int) -> Usuario | None:
        return self.db.get(Usuario, usuario_id)

    def obter_por_email(self, email: str) -> Usuario | None:
        return self.db.scalar(select(Usuario).where(func.lower(Usuario.email) == email.lower()))

    def adicionar(self, usuario: Usuario) -> Usuario:
        self.db.add(usuario)
        self.db.flush()
        return usuario
