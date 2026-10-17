from sqlalchemy.orm import Session

from app.core.excecoes import Conflito, NaoEncontrado
from app.models import Categoria, Usuario
from app.repositories.categoria import CategoriaRepositorio
from app.repositories.ocorrencia import OcorrenciaRepositorio
from app.schemas.categoria import CategoriaEntrada
from app.services.permissoes import exigir_gestor


class CategoriaServico:
    def __init__(self, db: Session):
        self.db = db
        self.categorias = CategoriaRepositorio(db)
        self.ocorrencias = OcorrenciaRepositorio(db)

    def listar(self, incluir_inativas: bool = False) -> list[Categoria]:
        return self.categorias.listar(incluir_inativas)

    def obter(self, categoria_id: int) -> Categoria:
        categoria = self.categorias.obter(categoria_id)
        if categoria is None:
            raise NaoEncontrado("Categoria não encontrada.", "CATEGORIA_NAO_ENCONTRADA")
        return categoria

    def criar(self, dados: CategoriaEntrada, usuario: Usuario) -> Categoria:
        exigir_gestor(usuario)
        self._exigir_nome_livre(dados.nome)
        categoria = self.categorias.adicionar(
            Categoria(nome=dados.nome, descricao=dados.descricao or None, ativa=dados.ativa)
        )
        self.db.commit()
        return categoria

    def alterar(self, categoria_id: int, dados: CategoriaEntrada, usuario: Usuario) -> Categoria:
        exigir_gestor(usuario)
        categoria = self.obter(categoria_id)
        self._exigir_nome_livre(dados.nome, ignorar_id=categoria.id)
        categoria.nome = dados.nome
        categoria.descricao = dados.descricao or None
        categoria.ativa = dados.ativa
        self.db.commit()
        return categoria

    def excluir(self, categoria_id: int, usuario: Usuario) -> None:
        exigir_gestor(usuario)
        categoria = self.obter(categoria_id)
        if self.ocorrencias.contar_por_categoria(categoria.id) > 0:
            raise Conflito(
                "A categoria possui ocorrências vinculadas. Desative-a em vez de excluir.",
                "CATEGORIA_EM_USO",
            )
        self.categorias.excluir(categoria)
        self.db.commit()

    def _exigir_nome_livre(self, nome: str, ignorar_id: int | None = None) -> None:
        existente = self.categorias.obter_por_nome(nome)
        if existente is not None and existente.id != ignorar_id:
            raise Conflito("Já existe uma categoria com esse nome.", "CATEGORIA_DUPLICADA")
