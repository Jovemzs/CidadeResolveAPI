from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.core.dependencias import UsuarioAtual, obter_auth_servico
from app.schemas.usuario import LoginEntrada, TokenSaida, UsuarioRegistro, UsuarioSaida
from app.services.auth import AuthServico

router = APIRouter(prefix="/auth", tags=["Autenticação"])

Servico = Annotated[AuthServico, Depends(obter_auth_servico)]


@router.post(
    "/registro",
    response_model=UsuarioSaida,
    status_code=status.HTTP_201_CREATED,
    summary="Cria usuário cidadão",
)
def registrar(dados: UsuarioRegistro, servico: Servico):
    return servico.registrar(dados)


@router.post("/login", response_model=TokenSaida, summary="Devolve token JWT")
def login(dados: LoginEntrada, servico: Servico):
    return TokenSaida(access_token=servico.autenticar(dados.email, dados.senha))


@router.get("/eu", response_model=UsuarioSaida, summary="Dados do usuário logado")
def eu(usuario: UsuarioAtual):
    return usuario
