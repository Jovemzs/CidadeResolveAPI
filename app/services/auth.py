from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.excecoes import Conflito, NaoAutenticado
from app.core.seguranca import criar_token, gerar_hash_senha, ler_token, verificar_senha
from app.models import Papel, Usuario
from app.repositories.usuario import UsuarioRepositorio
from app.schemas.usuario import UsuarioRegistro


class AuthServico:
    def __init__(self, db: Session):
        self.db = db
        self.usuarios = UsuarioRepositorio(db)

    def registrar(self, dados: UsuarioRegistro) -> Usuario:
        email = dados.email.lower()
        if self.usuarios.obter_por_email(email):
            raise Conflito("E-mail já cadastrado.", "EMAIL_JA_CADASTRADO")
        usuario = Usuario(
            nome=dados.nome,
            email=email,
            senha_hash=gerar_hash_senha(dados.senha),
            papel=Papel.CIDADAO,
        )
        try:
            self.usuarios.adicionar(usuario)
            self.db.commit()
        except IntegrityError:
            self.db.rollback()
            raise Conflito("E-mail já cadastrado.", "EMAIL_JA_CADASTRADO")
        return usuario

    def autenticar(self, email: str, senha: str) -> str:
        usuario = self.usuarios.obter_por_email(email.strip())
        if usuario is None or not verificar_senha(senha, usuario.senha_hash):
            raise NaoAutenticado("E-mail ou senha inválidos.", "CREDENCIAIS_INVALIDAS")
        return criar_token(usuario.id)

    def usuario_do_token(self, token: str) -> Usuario:
        usuario = self.usuarios.obter(ler_token(token))
        if usuario is None:
            raise NaoAutenticado("Token inválido ou expirado.", "TOKEN_INVALIDO")
        return usuario
