from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.core.dependencias import UsuarioAtual, obter_foto_servico
from app.services.foto import FotoServico

router = APIRouter(prefix="/fotos", tags=["Ocorrências"])


@router.delete(
    "/{foto_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Exclui foto (dono ou gestor)"
)
def excluir(
    foto_id: int, usuario: UsuarioAtual, servico: Annotated[FotoServico, Depends(obter_foto_servico)]
):
    servico.excluir(foto_id, usuario)
