"""Carga inicial idempotente: gestor e categorias padrão. Uso: python -m app.seed"""

from sqlalchemy.orm import Session

from app.core.config import obter_configuracoes
from app.core.seguranca import gerar_hash_senha
from app.db.sessao import SessaoLocal
from app.models import Categoria, Papel, Usuario
from app.repositories.categoria import CategoriaRepositorio
from app.repositories.usuario import UsuarioRepositorio

CATEGORIAS_PADRAO = [
    ("Buraco na via", "Buracos e defeitos no asfalto ou na calçada."),
    ("Iluminação pública", "Postes apagados, lâmpadas queimadas ou piscando."),
    ("Descarte irregular de lixo", "Lixo ou entulho descartado em local inadequado."),
]


def executar_carga(db: Session) -> None:
    config = obter_configuracoes()
    usuarios = UsuarioRepositorio(db)
    categorias = CategoriaRepositorio(db)

    if config.gestor_email and config.gestor_senha:
        email = config.gestor_email.lower()
        if usuarios.obter_por_email(email) is None:
            usuarios.adicionar(
                Usuario(
                    nome="Equipe de atendimento",
                    email=email,
                    senha_hash=gerar_hash_senha(config.gestor_senha),
                    papel=Papel.GESTOR,
                )
            )
            print(f"Gestor criado: {email}")
    else:
        print("GESTOR_EMAIL/GESTOR_SENHA não definidos: gestor não criado.")

    for nome, descricao in CATEGORIAS_PADRAO:
        if categorias.obter_por_nome(nome) is None:
            categorias.adicionar(Categoria(nome=nome, descricao=descricao))
            print(f"Categoria criada: {nome}")

    db.commit()


if __name__ == "__main__":
    with SessaoLocal() as sessao:
        executar_carga(sessao)
