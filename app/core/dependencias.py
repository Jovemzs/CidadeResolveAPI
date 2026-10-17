from collections.abc import Iterator
from functools import lru_cache
from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.config import obter_configuracoes
from app.core.excecoes import NaoAutenticado
from app.db.sessao import SessaoLocal
from app.models import Usuario
from app.services.armazenamento import ArmazenamentoFotos, ArmazenamentoFotosDisco
from app.services.auth import AuthServico
from app.services.categoria import CategoriaServico
from app.services.foto import FotoServico
from app.services.indicadores import IndicadoresServico
from app.services.ocorrencia import OcorrenciaServico

esquema_bearer = HTTPBearer(auto_error=False, description="Token JWT obtido em /api/v1/auth/login")


def obter_db() -> Iterator[Session]:
    db = SessaoLocal()
    try:
        yield db
    finally:
        db.close()


SessaoDb = Annotated[Session, Depends(obter_db)]
Credenciais = Annotated[HTTPAuthorizationCredentials | None, Depends(esquema_bearer)]


@lru_cache
def obter_armazenamento() -> ArmazenamentoFotos:
    return ArmazenamentoFotosDisco(obter_configuracoes().upload_dir)


Armazenamento = Annotated[ArmazenamentoFotos, Depends(obter_armazenamento)]


def obter_auth_servico(db: SessaoDb) -> AuthServico:
    return AuthServico(db)


def obter_categoria_servico(db: SessaoDb) -> CategoriaServico:
    return CategoriaServico(db)


def obter_ocorrencia_servico(db: SessaoDb, armazenamento: Armazenamento) -> OcorrenciaServico:
    return OcorrenciaServico(db, armazenamento)


def obter_foto_servico(db: SessaoDb, armazenamento: Armazenamento) -> FotoServico:
    return FotoServico(db, armazenamento)


def obter_indicadores_servico(db: SessaoDb) -> IndicadoresServico:
    return IndicadoresServico(db)


def obter_usuario_opcional(
    credenciais: Credenciais, servico: Annotated[AuthServico, Depends(obter_auth_servico)]
) -> Usuario | None:
    """Sem token devolve None; com token inválido levanta NaoAutenticado."""
    if credenciais is None:
        return None
    return servico.usuario_do_token(credenciais.credentials)


def obter_usuario_atual(
    usuario: Annotated[Usuario | None, Depends(obter_usuario_opcional)],
) -> Usuario:
    if usuario is None:
        raise NaoAutenticado("Autenticação necessária.")
    return usuario


UsuarioAtual = Annotated[Usuario, Depends(obter_usuario_atual)]
UsuarioOpcional = Annotated[Usuario | None, Depends(obter_usuario_opcional)]
