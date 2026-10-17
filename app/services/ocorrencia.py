from sqlalchemy.orm import Session

from app.core.excecoes import Conflito, DadosInvalidos, NaoAutenticado, NaoEncontrado
from app.db.base import agora
from app.models import Categoria, HistoricoStatus, Ocorrencia, StatusOcorrencia, Usuario
from app.repositories.categoria import CategoriaRepositorio
from app.repositories.historico_status import HistoricoStatusRepositorio
from app.repositories.ocorrencia import OcorrenciaRepositorio
from app.schemas.ocorrencia import OcorrenciaEntrada, StatusEntrada
from app.services.armazenamento import ArmazenamentoFotos
from app.services.permissoes import exigir_gestor, exigir_pode_modificar

TRANSICOES: dict[StatusOcorrencia, set[StatusOcorrencia]] = {
    StatusOcorrencia.ABERTA: {StatusOcorrencia.EM_ANALISE, StatusOcorrencia.REJEITADA},
    StatusOcorrencia.EM_ANALISE: {StatusOcorrencia.EM_ATENDIMENTO, StatusOcorrencia.REJEITADA},
    StatusOcorrencia.EM_ATENDIMENTO: {StatusOcorrencia.RESOLVIDA},
    StatusOcorrencia.RESOLVIDA: set(),
    StatusOcorrencia.REJEITADA: set(),
}


class OcorrenciaServico:
    def __init__(self, db: Session, armazenamento: ArmazenamentoFotos):
        self.db = db
        self.armazenamento = armazenamento
        self.ocorrencias = OcorrenciaRepositorio(db)
        self.categorias = CategoriaRepositorio(db)
        self.historicos = HistoricoStatusRepositorio(db)

    def listar(
        self,
        *,
        bairro: str | None,
        categoria_id: int | None,
        status: StatusOcorrencia | None,
        minhas: bool,
        usuario: Usuario | None,
        pagina: int,
        tamanho: int,
    ) -> tuple[list[Ocorrencia], int]:
        autor_id = None
        if minhas:
            if usuario is None:
                raise NaoAutenticado("O filtro 'minhas' exige login.")
            autor_id = usuario.id
        return self.ocorrencias.listar(
            bairro=bairro,
            categoria_id=categoria_id,
            status=status,
            autor_id=autor_id,
            pagina=pagina,
            tamanho=tamanho,
        )

    def obter(self, ocorrencia_id: int) -> Ocorrencia:
        ocorrencia = self.ocorrencias.obter(ocorrencia_id)
        if ocorrencia is None:
            raise NaoEncontrado("Ocorrência não encontrada.", "OCORRENCIA_NAO_ENCONTRADA")
        return ocorrencia

    def criar(self, dados: OcorrenciaEntrada, usuario: Usuario) -> Ocorrencia:
        categoria = self._obter_categoria_ativa(dados.categoria_id)
        ocorrencia = Ocorrencia(
            titulo=dados.titulo,
            descricao=dados.descricao,
            categoria=categoria,
            autor=usuario,
            status=StatusOcorrencia.ABERTA,
            endereco=dados.endereco,
            bairro=dados.bairro,
            latitude=dados.latitude,
            longitude=dados.longitude,
        )
        self.ocorrencias.adicionar(ocorrencia)
        self.historicos.adicionar(
            HistoricoStatus(
                ocorrencia_id=ocorrencia.id,
                status_anterior=None,
                status_novo=StatusOcorrencia.ABERTA,
                alterado_por_id=usuario.id,
            )
        )
        self.db.commit()
        return self.obter(ocorrencia.id)

    def alterar(self, ocorrencia_id: int, dados: OcorrenciaEntrada, usuario: Usuario) -> Ocorrencia:
        ocorrencia = self.obter(ocorrencia_id)
        exigir_pode_modificar(usuario, ocorrencia)
        if dados.categoria_id != ocorrencia.categoria_id:
            ocorrencia.categoria = self._obter_categoria_ativa(dados.categoria_id)
        ocorrencia.titulo = dados.titulo
        ocorrencia.descricao = dados.descricao
        ocorrencia.endereco = dados.endereco
        ocorrencia.bairro = dados.bairro
        ocorrencia.latitude = dados.latitude
        ocorrencia.longitude = dados.longitude
        self.db.commit()
        return self.obter(ocorrencia.id)

    def excluir(self, ocorrencia_id: int, usuario: Usuario) -> None:
        ocorrencia = self.obter(ocorrencia_id)
        exigir_pode_modificar(usuario, ocorrencia)
        arquivos = [foto.nome_arquivo for foto in ocorrencia.fotos]
        self.ocorrencias.excluir(ocorrencia)
        self.db.commit()
        for nome_arquivo in arquivos:
            self.armazenamento.excluir(nome_arquivo)

    def mudar_status(self, ocorrencia_id: int, dados: StatusEntrada, usuario: Usuario) -> Ocorrencia:
        exigir_gestor(usuario)
        ocorrencia = self.obter(ocorrencia_id)
        atual, novo = ocorrencia.status, dados.status
        if novo not in TRANSICOES[atual]:
            raise Conflito(
                f"Não é possível ir de {atual.value} para {novo.value}.", "TRANSICAO_INVALIDA"
            )
        if novo == StatusOcorrencia.REJEITADA and not dados.comentario:
            raise DadosInvalidos(
                "É obrigatório informar um comentário ao rejeitar.", "COMENTARIO_OBRIGATORIO"
            )
        ocorrencia.status = novo
        if novo == StatusOcorrencia.RESOLVIDA:
            ocorrencia.resolvido_em = agora()
        self.historicos.adicionar(
            HistoricoStatus(
                ocorrencia_id=ocorrencia.id,
                status_anterior=atual,
                status_novo=novo,
                alterado_por_id=usuario.id,
                comentario=dados.comentario or None,
            )
        )
        self.db.commit()
        return self.obter(ocorrencia.id)

    def historico(self, ocorrencia_id: int) -> list[HistoricoStatus]:
        self.obter(ocorrencia_id)
        return self.historicos.listar_por_ocorrencia(ocorrencia_id)

    def _obter_categoria_ativa(self, categoria_id: int) -> Categoria:
        categoria = self.categorias.obter(categoria_id)
        if categoria is None or not categoria.ativa:
            raise DadosInvalidos(
                "Categoria inexistente ou inativa.", "CATEGORIA_INVALIDA"
            )
        return categoria
