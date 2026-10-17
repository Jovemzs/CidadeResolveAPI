from app.core.excecoes import SemPermissao
from app.models import Ocorrencia, StatusOcorrencia, Usuario


def exigir_gestor(usuario: Usuario) -> None:
    if not usuario.eh_gestor:
        raise SemPermissao("Ação restrita a gestores.")


def exigir_pode_modificar(usuario: Usuario, ocorrencia: Ocorrencia) -> None:
    """Gestor pode sempre; cidadão só nas próprias ocorrências e só em ABERTA."""
    if usuario.eh_gestor:
        return
    if ocorrencia.autor_id != usuario.id:
        raise SemPermissao("Você só pode alterar as suas próprias ocorrências.")
    if ocorrencia.status != StatusOcorrencia.ABERTA:
        raise SemPermissao("A ocorrência só pode ser alterada enquanto estiver ABERTA.")
