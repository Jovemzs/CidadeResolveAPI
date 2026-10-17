import os
import shutil
import tempfile
from pathlib import Path

# As variáveis precisam estar definidas antes de importar a aplicação.
URL_TESTE = os.environ.get(
    "TEST_DATABASE_URL",
    "postgresql+psycopg://cidaderesolve:cidaderesolve@localhost:5440/cidaderesolve_test",
)
DIRETORIO_UPLOADS = Path(tempfile.mkdtemp(prefix="cidaderesolve-uploads-"))
os.environ["DATABASE_URL"] = URL_TESTE
os.environ["JWT_SECRET"] = "segredo-usado-apenas-nos-testes-automatizados"
os.environ["JWT_EXPIRA_MINUTOS"] = "60"
os.environ["UPLOAD_DIR"] = str(DIRETORIO_UPLOADS)

import pytest  # noqa: E402
from alembic import command  # noqa: E402
from alembic.config import Config  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine, text  # noqa: E402
from sqlalchemy.engine import make_url  # noqa: E402

from app.core.seguranca import criar_token, gerar_hash_senha  # noqa: E402
from app.db.base import Base  # noqa: E402
from app.db.sessao import SessaoLocal, engine  # noqa: E402
from app.main import app  # noqa: E402
from app.models import Categoria, Papel, Usuario  # noqa: E402

RAIZ = Path(__file__).resolve().parent.parent

PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64
JPEG = b"\xff\xd8\xff\xe0" + b"\x00" * 64
WEBP = b"RIFF" + b"\x00\x00\x00\x00" + b"WEBP" + b"\x00" * 64


@pytest.fixture(scope="session", autouse=True)
def banco_de_teste():
    """Recria o banco de teste a cada execução e aplica as migrações."""
    url = make_url(URL_TESTE)
    administracao = create_engine(url.set(database="postgres"), isolation_level="AUTOCOMMIT")
    with administracao.connect() as conexao:
        conexao.execute(text(f'DROP DATABASE IF EXISTS "{url.database}" WITH (FORCE)'))
        conexao.execute(text(f'CREATE DATABASE "{url.database}"'))
    administracao.dispose()

    configuracao = Config(str(RAIZ / "alembic.ini"))
    configuracao.set_main_option("script_location", str(RAIZ / "alembic"))
    configuracao.attributes["configurar_logs"] = False
    command.upgrade(configuracao, "head")

    yield

    engine.dispose()
    shutil.rmtree(DIRETORIO_UPLOADS, ignore_errors=True)


@pytest.fixture(autouse=True)
def limpar_dados():
    tabelas = ", ".join(tabela.name for tabela in Base.metadata.sorted_tables)
    with engine.begin() as conexao:
        conexao.execute(text(f"TRUNCATE {tabelas} RESTART IDENTITY CASCADE"))
    for arquivo in DIRETORIO_UPLOADS.iterdir():
        arquivo.unlink()
    yield


@pytest.fixture
def cliente():
    with TestClient(app) as cliente_teste:
        yield cliente_teste


@pytest.fixture
def db():
    with SessaoLocal() as sessao:
        yield sessao


@pytest.fixture
def diretorio_uploads() -> Path:
    return DIRETORIO_UPLOADS


def criar_usuario(db, email: str, papel: Papel = Papel.CIDADAO, nome: str = "Usuário") -> Usuario:
    usuario = Usuario(
        nome=nome, email=email, senha_hash=gerar_hash_senha("senha12345"), papel=papel
    )
    db.add(usuario)
    db.commit()
    return usuario


def cabecalho(usuario: Usuario) -> dict[str, str]:
    return {"Authorization": f"Bearer {criar_token(usuario.id)}"}


@pytest.fixture
def cidadao(db) -> Usuario:
    return criar_usuario(db, "ana@example.com", nome="Ana Cidadã")


@pytest.fixture
def outro_cidadao(db) -> Usuario:
    return criar_usuario(db, "bruno@example.com", nome="Bruno Vizinho")


@pytest.fixture
def gestor(db) -> Usuario:
    return criar_usuario(db, "gestor@example.com", Papel.GESTOR, nome="Gestora Carla")


@pytest.fixture
def auth_cidadao(cidadao) -> dict[str, str]:
    return cabecalho(cidadao)


@pytest.fixture
def auth_outro(outro_cidadao) -> dict[str, str]:
    return cabecalho(outro_cidadao)


@pytest.fixture
def auth_gestor(gestor) -> dict[str, str]:
    return cabecalho(gestor)


@pytest.fixture
def categoria(db) -> Categoria:
    registro = Categoria(nome="Buraco na via", descricao="Buracos no asfalto")
    db.add(registro)
    db.commit()
    return registro


@pytest.fixture
def outra_categoria(db) -> Categoria:
    registro = Categoria(nome="Iluminação pública")
    db.add(registro)
    db.commit()
    return registro


def dados_ocorrencia(categoria_id: int, **alteracoes) -> dict:
    dados = {
        "titulo": "Buraco grande na rua",
        "descricao": "Há um buraco fundo em frente ao número 120.",
        "categoria_id": categoria_id,
        "endereco": "Rua das Flores, 120",
        "bairro": "Centro",
        "latitude": -23.55052,
        "longitude": -46.633308,
    }
    dados.update(alteracoes)
    return dados


@pytest.fixture
def nova_ocorrencia(cliente, categoria, auth_cidadao):
    """Função que cria uma ocorrência pela API e devolve o JSON da resposta."""

    def criar(auth: dict | None = None, **alteracoes) -> dict:
        alteracoes.setdefault("categoria_id", categoria.id)
        resposta = cliente.post(
            "/api/v1/ocorrencias",
            json=dados_ocorrencia(**alteracoes),
            headers=auth or auth_cidadao,
        )
        assert resposta.status_code == 201, resposta.text
        return resposta.json()

    return criar


@pytest.fixture
def mudar_status(cliente, auth_gestor):
    def mudar(ocorrencia_id: int, *sequencia: str, comentario: str | None = None):
        resposta = None
        for status in sequencia:
            resposta = cliente.patch(
                f"/api/v1/ocorrencias/{ocorrencia_id}/status",
                json={"status": status, "comentario": comentario},
                headers=auth_gestor,
            )
        return resposta

    return mudar
