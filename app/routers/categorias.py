from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.core.dependencias import UsuarioAtual, obter_categoria_servico
from app.schemas.categoria import CategoriaEntrada, CategoriaSaida
from app.services.categoria import CategoriaServico

router = APIRouter(prefix="/categorias", tags=["Categorias"])

Servico = Annotated[CategoriaServico, Depends(obter_categoria_servico)]


@router.get("", response_model=list[CategoriaSaida], summary="Lista categorias")
def listar(
    servico: Servico,
    incluir_inativas: Annotated[
        bool, Query(description="Inclui também as categorias desativadas")
    ] = False,
):
    return servico.listar(incluir_inativas)


@router.get("/{categoria_id}", response_model=CategoriaSaida, summary="Detalha categoria")
def obter(categoria_id: int, servico: Servico):
    return servico.obter(categoria_id)


@router.post(
    "",
    response_model=CategoriaSaida,
    status_code=status.HTTP_201_CREATED,
    summary="Cria categoria (gestor)",
)
def criar(dados: CategoriaEntrada, usuario: UsuarioAtual, servico: Servico):
    return servico.criar(dados, usuario)


@router.put("/{categoria_id}", response_model=CategoriaSaida, summary="Altera categoria (gestor)")
def alterar(categoria_id: int, dados: CategoriaEntrada, usuario: UsuarioAtual, servico: Servico):
    return servico.alterar(categoria_id, dados, usuario)


@router.delete(
    "/{categoria_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Exclui categoria sem ocorrências (gestor)",
)
def excluir(categoria_id: int, usuario: UsuarioAtual, servico: Servico):
    servico.excluir(categoria_id, usuario)
