from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from app.core.config import obter_configuracoes
from app.core.excecoes import NaoAutenticado

ALGORITMO = "HS256"


def gerar_hash_senha(senha: str) -> str:
    return bcrypt.hashpw(senha.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verificar_senha(senha: str, senha_hash: str) -> bool:
    try:
        return bcrypt.checkpw(senha.encode("utf-8"), senha_hash.encode("utf-8"))
    except ValueError:
        return False


def criar_token(usuario_id: int) -> str:
    config = obter_configuracoes()
    expira_em = datetime.now(timezone.utc) + timedelta(minutes=config.jwt_expira_minutos)
    return jwt.encode({"sub": str(usuario_id), "exp": expira_em}, config.jwt_secret, algorithm=ALGORITMO)


def ler_token(token: str) -> int:
    """Devolve o id do usuário do token ou levanta NaoAutenticado."""
    try:
        dados = jwt.decode(token, obter_configuracoes().jwt_secret, algorithms=[ALGORITMO])
        return int(dados["sub"])
    except (jwt.PyJWTError, KeyError, ValueError):
        raise NaoAutenticado("Token inválido ou expirado.", "TOKEN_INVALIDO")
