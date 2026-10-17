import pytest

from tests.conftest import JPEG, PNG, WEBP

URL = "/api/v1/ocorrencias"
CINCO_MB = 5 * 1024 * 1024


def enviar(cliente, ocorrencia_id, auth, conteudo=PNG, nome="foto.png", tipo="image/png"):
    return cliente.post(
        f"{URL}/{ocorrencia_id}/fotos", files={"arquivo": (nome, conteudo, tipo)}, headers=auth
    )


@pytest.mark.parametrize(
    "conteudo,tipo,extensao",
    [(PNG, "image/png", ".png"), (JPEG, "image/jpeg", ".jpg"), (WEBP, "image/webp", ".webp")],
)
def test_upload_valido(
    cliente, nova_ocorrencia, auth_cidadao, diretorio_uploads, conteudo, tipo, extensao
):
    ocorrencia = nova_ocorrencia()

    resposta = enviar(cliente, ocorrencia["id"], auth_cidadao, conteudo, "minha foto.bin", tipo)

    assert resposta.status_code == 201
    foto = resposta.json()
    assert foto["tipo_conteudo"] == tipo
    assert foto["tamanho_bytes"] == len(conteudo)
    # Nome gerado pelo servidor, nunca o enviado pelo cliente.
    nome_arquivo = foto["url"].rsplit("/", 1)[1]
    assert foto["url"] == f"http://testserver/uploads/{nome_arquivo}"
    assert nome_arquivo.endswith(extensao)
    assert "minha" not in nome_arquivo
    assert (diretorio_uploads / nome_arquivo).read_bytes() == conteudo
    # A URL devolvida serve o arquivo.
    assert cliente.get(foto["url"]).content == conteudo


def test_foto_aparece_no_detalhe_da_ocorrencia(cliente, nova_ocorrencia, auth_cidadao):
    ocorrencia = nova_ocorrencia()
    foto = enviar(cliente, ocorrencia["id"], auth_cidadao).json()

    detalhe = cliente.get(f"{URL}/{ocorrencia['id']}").json()

    assert detalhe["fotos"] == [foto]


def test_tipo_invalido_mesmo_com_extensao_de_imagem(
    cliente, nova_ocorrencia, auth_cidadao, diretorio_uploads
):
    ocorrencia = nova_ocorrencia()

    resposta = enviar(cliente, ocorrencia["id"], auth_cidadao, b"%PDF-1.7 isto nao e imagem")

    assert resposta.status_code == 400
    assert resposta.json()["erro"]["codigo"] == "TIPO_DE_ARQUIVO_INVALIDO"
    assert list(diretorio_uploads.iterdir()) == []


def test_tamanho_no_limite_e_aceito(cliente, nova_ocorrencia, auth_cidadao):
    ocorrencia = nova_ocorrencia()
    conteudo = PNG + b"\x00" * (CINCO_MB - len(PNG))

    resposta = enviar(cliente, ocorrencia["id"], auth_cidadao, conteudo)

    assert resposta.status_code == 201
    assert resposta.json()["tamanho_bytes"] == CINCO_MB


def test_tamanho_excedido(cliente, nova_ocorrencia, auth_cidadao, diretorio_uploads):
    ocorrencia = nova_ocorrencia()
    conteudo = PNG + b"\x00" * (CINCO_MB - len(PNG) + 1)

    resposta = enviar(cliente, ocorrencia["id"], auth_cidadao, conteudo)

    assert resposta.status_code == 400
    assert resposta.json()["erro"]["codigo"] == "ARQUIVO_MUITO_GRANDE"
    assert list(diretorio_uploads.iterdir()) == []


def test_limite_de_cinco_fotos(cliente, nova_ocorrencia, auth_cidadao):
    ocorrencia = nova_ocorrencia()
    for _ in range(5):
        assert enviar(cliente, ocorrencia["id"], auth_cidadao).status_code == 201

    resposta = enviar(cliente, ocorrencia["id"], auth_cidadao)

    assert resposta.status_code == 409
    assert resposta.json()["erro"]["codigo"] == "LIMITE_DE_FOTOS"
    assert len(cliente.get(f"{URL}/{ocorrencia['id']}").json()["fotos"]) == 5


def test_upload_permissoes(cliente, nova_ocorrencia, auth_outro, auth_gestor):
    ocorrencia = nova_ocorrencia()

    assert enviar(cliente, ocorrencia["id"], None).status_code == 401
    assert enviar(cliente, ocorrencia["id"], auth_outro).status_code == 403
    assert enviar(cliente, ocorrencia["id"], auth_gestor).status_code == 201


def test_dono_nao_envia_nem_exclui_foto_fora_de_aberta(
    cliente, nova_ocorrencia, auth_cidadao, auth_gestor, mudar_status
):
    ocorrencia = nova_ocorrencia()
    foto = enviar(cliente, ocorrencia["id"], auth_cidadao).json()
    mudar_status(ocorrencia["id"], "EM_ANALISE")

    assert enviar(cliente, ocorrencia["id"], auth_cidadao).status_code == 403
    assert cliente.delete(f"/api/v1/fotos/{foto['id']}", headers=auth_cidadao).status_code == 403
    assert cliente.delete(f"/api/v1/fotos/{foto['id']}", headers=auth_gestor).status_code == 204


def test_upload_em_ocorrencia_inexistente(cliente, auth_cidadao):
    assert enviar(cliente, 999, auth_cidadao).status_code == 404


def test_excluir_foto_remove_registro_e_arquivo(
    cliente, nova_ocorrencia, auth_cidadao, diretorio_uploads
):
    ocorrencia = nova_ocorrencia()
    foto = enviar(cliente, ocorrencia["id"], auth_cidadao).json()

    resposta = cliente.delete(f"/api/v1/fotos/{foto['id']}", headers=auth_cidadao)

    assert resposta.status_code == 204
    assert cliente.get(f"{URL}/{ocorrencia['id']}").json()["fotos"] == []
    assert list(diretorio_uploads.iterdir()) == []


def test_excluir_foto_permissoes(cliente, nova_ocorrencia, auth_cidadao, auth_outro):
    ocorrencia = nova_ocorrencia()
    foto = enviar(cliente, ocorrencia["id"], auth_cidadao).json()

    assert cliente.delete(f"/api/v1/fotos/{foto['id']}").status_code == 401
    assert cliente.delete(f"/api/v1/fotos/{foto['id']}", headers=auth_outro).status_code == 403
    assert cliente.delete("/api/v1/fotos/999", headers=auth_cidadao).status_code == 404


def test_excluir_ocorrencia_remove_arquivos_das_fotos(
    cliente, db, nova_ocorrencia, auth_cidadao, diretorio_uploads
):
    from app.models import Foto

    ocorrencia = nova_ocorrencia()
    enviar(cliente, ocorrencia["id"], auth_cidadao)
    enviar(cliente, ocorrencia["id"], auth_cidadao, JPEG)
    assert len(list(diretorio_uploads.iterdir())) == 2

    resposta = cliente.delete(f"{URL}/{ocorrencia['id']}", headers=auth_cidadao)

    assert resposta.status_code == 204
    assert list(diretorio_uploads.iterdir()) == []
    assert db.query(Foto).count() == 0
