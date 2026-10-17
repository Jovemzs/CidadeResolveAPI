from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
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
                "mensagem": item["msg"],
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

    for modulo in (auth, categorias, ocorrencias, fotos, indicadores):
        app.include_router(modulo.router, prefix=PREFIXO)

    @app.get("/saude", tags=["Infraestrutura"], summary="Verifica se a API está no ar")
    def saude():
        return {"status": "ok"}

    diretorio_uploads = Path(obter_configuracoes().upload_dir)
    diretorio_uploads.mkdir(parents=True, exist_ok=True)
    app.mount("/uploads", StaticFiles(directory=diretorio_uploads), name="uploads")

    return app


app = criar_aplicacao()
