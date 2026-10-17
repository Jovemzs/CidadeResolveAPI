import uuid

from sqlalchemy.orm import Session

from app.core.excecoes import ArquivoInvalido, Conflito, NaoEncontrado
from app.models import Foto, Usuario
from app.repositories.foto import FotoRepositorio
from app.repositories.ocorrencia import OcorrenciaRepositorio
from app.services.armazenamento import ArmazenamentoFotos
from app.services.permissoes import exigir_pode_modificar

TAMANHO_MAXIMO_BYTES = 5 * 1024 * 1024
MAXIMO_FOTOS_POR_OCORRENCIA = 5


def detectar_tipo(conteudo: bytes) -> tuple[str, str] | None:
    """Identifica o tipo pela assinatura do arquivo. Devolve (tipo_conteudo, extensão)."""
    if conteudo.startswith(b"\xff\xd8\xff"):
        return "image/jpeg", ".jpg"
    if conteudo.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png", ".png"
    if conteudo[:4] == b"RIFF" and conteudo[8:12] == b"WEBP":
        return "image/webp", ".webp"
    return None


class FotoServico:
    def __init__(self, db: Session, armazenamento: ArmazenamentoFotos):
        self.db = db
        self.armazenamento = armazenamento
        self.fotos = FotoRepositorio(db)
        self.ocorrencias = OcorrenciaRepositorio(db)

    def adicionar(self, ocorrencia_id: int, conteudo: bytes, usuario: Usuario) -> Foto:
        ocorrencia = self.ocorrencias.obter(ocorrencia_id)
        if ocorrencia is None:
            raise NaoEncontrado("Ocorrência não encontrada.", "OCORRENCIA_NAO_ENCONTRADA")
        exigir_pode_modificar(usuario, ocorrencia)

        if len(conteudo) > TAMANHO_MAXIMO_BYTES:
            raise ArquivoInvalido("A foto deve ter no máximo 5 MB.", "ARQUIVO_MUITO_GRANDE")
        tipo = detectar_tipo(conteudo)
        if tipo is None:
            raise ArquivoInvalido(
                "Tipo de arquivo não aceito. Envie JPEG, PNG ou WebP.", "TIPO_DE_ARQUIVO_INVALIDO"
            )
        if self.fotos.contar_por_ocorrencia(ocorrencia.id) >= MAXIMO_FOTOS_POR_OCORRENCIA:
            raise Conflito(
                f"A ocorrência já tem o máximo de {MAXIMO_FOTOS_POR_OCORRENCIA} fotos.",
                "LIMITE_DE_FOTOS",
            )

        tipo_conteudo, extensao = tipo
        nome_arquivo = f"{uuid.uuid4().hex}{extensao}"
        self.armazenamento.salvar(nome_arquivo, conteudo)
        try:
            foto = self.fotos.adicionar(
                Foto(
                    ocorrencia_id=ocorrencia.id,
                    nome_arquivo=nome_arquivo,
                    tipo_conteudo=tipo_conteudo,
                    tamanho_bytes=len(conteudo),
                )
            )
            self.db.commit()
        except Exception:
            self.db.rollback()
            self.armazenamento.excluir(nome_arquivo)
            raise
        return foto

    def excluir(self, foto_id: int, usuario: Usuario) -> None:
        foto = self.fotos.obter(foto_id)
        if foto is None:
            raise NaoEncontrado("Foto não encontrada.", "FOTO_NAO_ENCONTRADA")
        exigir_pode_modificar(usuario, foto.ocorrencia)
        nome_arquivo = foto.nome_arquivo
        self.fotos.excluir(foto)
        self.db.commit()
        self.armazenamento.excluir(nome_arquivo)
