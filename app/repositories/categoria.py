from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Categoria


class CategoriaRepositorio:
    def __init__(self, db: Session):
        self.db = db

    def listar(self, incluir_inativas: bool = False) -> list[Categoria]:
        consulta = select(Categoria).order_by(Categoria.nome)
        if not incluir_inativas:
            consulta = consulta.where(Categoria.ativa.is_(True))
        return list(self.db.scalars(consulta))

    def obter(self, categoria_id: int) -> Categoria | None:
        return self.db.get(Categoria, categoria_id)

    def obter_por_nome(self, nome: str) -> Categoria | None:
        return self.db.scalar(select(Categoria).where(func.lower(Categoria.nome) == nome.lower()))

    def adicionar(self, categoria: Categoria) -> Categoria:
        self.db.add(categoria)
        self.db.flush()
        return categoria

    def excluir(self, categoria: Categoria) -> None:
        self.db.delete(categoria)
        self.db.flush()
