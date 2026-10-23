from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.config import obter_configuracoes
from app.core.excecoes import (
    ArquivoInvalido,
    Conflito,
    DadosInvalidos,
    ErroNegocio,
    NaoAutenticado,
    NaoEncontrado,
    SemPermissao,
)
from app.routers import auth, categorias, fotos, indicadores, ocorrencias

PREFIXO = "/api/v1"

STATUS_POR_ERRO: dict[type[ErroNegocio], int] = {
    ArquivoInvalido: 400,
    NaoAutenticado: 401,
    SemPermissao: 403,
    NaoEncontrado: 404,
    Conflito: 409,
    DadosInvalidos: 422,
}

CODIGO_POR_STATUS = {401: "NAO_AUTENTICADO", 403: "SEM_PERMISSAO", 404: "NAO_ENCONTRADO"}

DIRETORIO_FRONTEND = Path(__file__).resolve().parent.parent / "frontend"

MENSAGENS_VALIDACAO = {
    "missing": "Campo obrigatório.",
    "string_too_short": "Deve ter pelo menos {min_length} caractere(s).",
    "string_too_long": "Deve ter no máximo {max_length} caracteres.",
    "greater_than_equal": "Deve ser maior ou igual a {ge}.",
    "less_than_equal": "Deve ser menor ou igual a {le}.",
    "int_parsing": "Informe um número inteiro.",
    "int_type": "Informe um número inteiro.",
    "float_parsing": "Informe um número.",
    "float_type": "Informe um número.",
    "string_type": "Informe um texto.",
    "bool_parsing": "Informe verdadeiro ou falso.",
    "enum": "Valor inválido. Opções: {expected}.",
    "date_parsing": "Informe uma data no formato AAAA-MM-DD.",
    "date_from_datetime_parsing": "Informe uma data no formato AAAA-MM-DD.",
    "json_invalid": "O corpo da requisição não é um JSON válido.",
}


def traduzir_erro_validacao(item: dict) -> str:
    tipo, contexto = item["type"], item.get("ctx") or {}
    if item.get("input", "") is None and tipo.endswith("_type"):
        return "Campo obrigatório."
    if tipo == "value_error":
        if "email" in item["msg"]:
            return "Informe um e-mail válido."
        return str(contexto.get("error", item["msg"]))
    modelo = MENSAGENS_VALIDACAO.get(tipo)
    if modelo is None:
        return item["msg"]
    try:
        return modelo.format(**contexto)
    except (KeyError, IndexError):
        return item["msg"]


def resposta_erro(status: int, codigo: str, mensagem: str, **extras) -> JSONResponse:
    return JSONResponse(
        status_code=status, content={"erro": {"codigo": codigo, "mensagem": mensagem, **extras}}
    )


def registrar_handlers(app: FastAPI) -> None:
    @app.exception_handler(ErroNegocio)
    async def tratar_erro_negocio(request: Request, erro: ErroNegocio):
        status = next(
            (codigo for tipo, codigo in STATUS_POR_ERRO.items() if isinstance(erro, tipo)), 400
        )
        resposta = resposta_erro(status, erro.codigo, erro.mensagem)
        if status == 401:
            resposta.headers["WWW-Authenticate"] = "Bearer"
        return resposta

    @app.exception_handler(RequestValidationError)
    async def tratar_validacao(request: Request, erro: RequestValidationError):
        detalhes = [
            {
                "campo": ".".join(str(parte) for parte in item["loc"] if parte != "body"),
                "mensagem": traduzir_erro_validacao(item),
            }
            for item in erro.errors()
        ]
        return resposta_erro(422, "DADOS_INVALIDOS", "Dados inválidos.", detalhes=detalhes)

    @app.exception_handler(StarletteHTTPException)
    async def tratar_http(request: Request, erro: StarletteHTTPException):
        codigo = CODIGO_POR_STATUS.get(erro.status_code, "ERRO_HTTP")
        return resposta_erro(erro.status_code, codigo, str(erro.detail))


def criar_aplicacao() -> FastAPI:
    app = FastAPI(
        title="CidadeResolve API",
        description=(
            "Web Service REST para registrar e acompanhar ocorrências urbanas. "
            "Protótipo acadêmico, sem integração oficial com prefeituras."
        ),
        version="1.0.0",
    )
    registrar_handlers(app)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=obter_configuracoes().lista_cors_origens,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    for modulo in (auth, categorias, ocorrencias, fotos, indicadores):
        app.include_router(modulo.router, prefix=PREFIXO)

    @app.get("/saude", tags=["Infraestrutura"], summary="Verifica se a API está no ar")
    def saude():
        return {"status": "ok"}

    diretorio_uploads = Path(obter_configuracoes().upload_dir)
    diretorio_uploads.mkdir(parents=True, exist_ok=True)
    app.mount("/uploads", StaticFiles(directory=diretorio_uploads), name="uploads")

    # O site (front-end) é servido na raiz. Fica por último para não encobrir as rotas acima.
    if DIRETORIO_FRONTEND.is_dir():
        app.mount("/", StaticFiles(directory=DIRETORIO_FRONTEND, html=True), name="site")

    return app


app = criar_aplicacao()
