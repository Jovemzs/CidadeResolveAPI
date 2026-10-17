from typing import Annotated

from fastapi import APIRouter, Depends, File, Query, Request, UploadFile, status

from app.core.dependencias import (
    UsuarioAtual,
    UsuarioOpcional,
    obter_foto_servico,
    obter_ocorrencia_servico,
)
from app.models import Foto, Ocorrencia, StatusOcorrencia
from app.schemas.ocorrencia import (
    FotoSaida,
    HistoricoSaida,
    OcorrenciaDetalhe,
    OcorrenciaEntrada,
    OcorrenciaSaida,
    PaginaOcorrencias,
    StatusEntrada,
)
from app.services.foto import TAMANHO_MAXIMO_BYTES, FotoServico
from app.services.ocorrencia import OcorrenciaServico

router = APIRouter(prefix="/ocorrencias", tags=["Ocorrências"])

Servico = Annotated[OcorrenciaServico, Depends(obter_ocorrencia_servico)]
ServicoFotos = Annotated[FotoServico, Depends(obter_foto_servico)]


def montar_foto(foto: Foto, request: Request) -> FotoSaida:
    return FotoSaida(
        id=foto.id,
        url=f"{str(request.base_url).rstrip('/')}/uploads/{foto.nome_arquivo}",
        tipo_conteudo=foto.tipo_conteudo,
        tamanho_bytes=foto.tamanho_bytes,
        criado_em=foto.criado_em,
    )


def montar_detalhe(ocorrencia: Ocorrencia, request: Request) -> OcorrenciaDetalhe:
    resumo = OcorrenciaSaida.model_validate(ocorrencia)
    return OcorrenciaDetalhe(
        **resumo.model_dump(), fotos=[montar_foto(foto, request) for foto in ocorrencia.fotos]
    )


@router.get("", response_model=PaginaOcorrencias, summary="Lista com filtros e paginação")
def listar(
    servico: Servico,
    usuario: UsuarioOpcional,
    bairro: Annotated[str | None, Query(description="Não diferencia maiúsculas")] = None,
    categoria_id: int | None = None,
    status: StatusOcorrencia | None = None,
    minhas: Annotated[bool, Query(description="Só as do usuário logado (exige login)")] = False,
    pagina: Annotated[int, Query(ge=1)] = 1,
    tamanho: Annotated[int, Query(ge=1, le=100)] = 20,
):
    itens, total = servico.listar(
        bairro=bairro,
        categoria_id=categoria_id,
        status=status,
        minhas=minhas,
        usuario=usuario,
        pagina=pagina,
        tamanho=tamanho,
    )
    return PaginaOcorrencias(itens=itens, total=total, pagina=pagina, tamanho=tamanho)


@router.get("/{ocorrencia_id}", response_model=OcorrenciaDetalhe, summary="Detalha, com fotos")
def obter(ocorrencia_id: int, request: Request, servico: Servico):
    return montar_detalhe(servico.obter(ocorrencia_id), request)


@router.post(
    "",
    response_model=OcorrenciaDetalhe,
    status_code=status.HTTP_201_CREATED,
    summary="Cria ocorrência",
)
def criar(dados: OcorrenciaEntrada, request: Request, usuario: UsuarioAtual, servico: Servico):
    return montar_detalhe(servico.criar(dados, usuario), request)


@router.put(
    "/{ocorrencia_id}", response_model=OcorrenciaDetalhe, summary="Altera ocorrência (dono ou gestor)"
)
def alterar(
    ocorrencia_id: int,
    dados: OcorrenciaEntrada,
    request: Request,
    usuario: UsuarioAtual,
    servico: Servico,
):
    return montar_detalhe(servico.alterar(ocorrencia_id, dados, usuario), request)


@router.delete(
    "/{ocorrencia_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Exclui ocorrência (dono ou gestor)",
)
def excluir(ocorrencia_id: int, usuario: UsuarioAtual, servico: Servico):
    servico.excluir(ocorrencia_id, usuario)


@router.patch(
    "/{ocorrencia_id}/status", response_model=OcorrenciaDetalhe, summary="Muda status (gestor)"
)
def mudar_status(
    ocorrencia_id: int,
    dados: StatusEntrada,
    request: Request,
    usuario: UsuarioAtual,
    servico: Servico,
):
    return montar_detalhe(servico.mudar_status(ocorrencia_id, dados, usuario), request)


@router.get(
    "/{ocorrencia_id}/historico",
    response_model=list[HistoricoSaida],
    summary="Histórico de status",
)
def historico(ocorrencia_id: int, servico: Servico):
    return servico.historico(ocorrencia_id)


@router.post(
    "/{ocorrencia_id}/fotos",
    response_model=FotoSaida,
    status_code=status.HTTP_201_CREATED,
    summary="Envia foto (dono ou gestor)",
)
def enviar_foto(
    ocorrencia_id: int,
    request: Request,
    usuario: UsuarioAtual,
    servico: ServicoFotos,
    arquivo: Annotated[UploadFile, File(description="Imagem JPEG, PNG ou WebP de até 5 MB")],
):
    # Lê um byte além do limite: basta para o serviço recusar sem carregar o arquivo inteiro.
    conteudo = arquivo.file.read(TAMANHO_MAXIMO_BYTES + 1)
    return montar_foto(servico.adicionar(ocorrencia_id, conteudo, usuario), request)
