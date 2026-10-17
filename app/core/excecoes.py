"""Exceções de negócio. Não conhecem HTTP: a conversão em resposta fica em main.py."""


class ErroNegocio(Exception):
    codigo = "ERRO_NEGOCIO"

    def __init__(self, mensagem: str, codigo: str | None = None):
        super().__init__(mensagem)
        self.mensagem = mensagem
        if codigo:
            self.codigo = codigo


class DadosInvalidos(ErroNegocio):
    codigo = "DADOS_INVALIDOS"


class ArquivoInvalido(ErroNegocio):
    codigo = "ARQUIVO_INVALIDO"


class NaoAutenticado(ErroNegocio):
    codigo = "NAO_AUTENTICADO"


class SemPermissao(ErroNegocio):
    codigo = "SEM_PERMISSAO"


class NaoEncontrado(ErroNegocio):
    codigo = "NAO_ENCONTRADO"


class Conflito(ErroNegocio):
    codigo = "CONFLITO"
