from abc import ABC, abstractmethod
from pathlib import Path


class ArmazenamentoFotos(ABC):
    """Onde os arquivos das fotos ficam guardados. Os serviços só conhecem esta interface."""

    @abstractmethod
    def salvar(self, nome_arquivo: str, conteudo: bytes) -> None: ...

    @abstractmethod
    def excluir(self, nome_arquivo: str) -> None: ...


class ArmazenamentoFotosDisco(ArmazenamentoFotos):
    def __init__(self, diretorio: str | Path):
        self.diretorio = Path(diretorio)
        self.diretorio.mkdir(parents=True, exist_ok=True)

    def salvar(self, nome_arquivo: str, conteudo: bytes) -> None:
        (self.diretorio / nome_arquivo).write_bytes(conteudo)

    def excluir(self, nome_arquivo: str) -> None:
        (self.diretorio / nome_arquivo).unlink(missing_ok=True)
