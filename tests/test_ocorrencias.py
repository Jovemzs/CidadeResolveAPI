import pytest

from tests.conftest import dados_ocorrencia

URL = "/api/v1/ocorrencias"


def test_criar_ocorrencia(cliente, categoria, cidadao, auth_cidadao):
    resposta = cliente.post(URL, json=dados_ocorrencia(categoria.id), headers=auth_cidadao)

    assert resposta.status_code == 201
    corpo = resposta.json()
    assert corpo["status"] == "ABERTA"
    assert corpo["categoria"] == {"id": categoria.id, "nome": "Buraco na via"}
    assert corpo["autor"] == {"id": cidadao.id, "nome": "Ana Cidadã"}
    assert corpo["latitude"] == pytest.approx(-23.55052)
    assert corpo["fotos"] == []
    assert corpo["resolvido_em"] is None


def test_criar_exige_login(cliente, categoria):
    resposta = cliente.post(URL, json=dados_ocorrencia(categoria.id))

    assert resposta.status_code == 401


@pytest.mark.parametrize(
    "alteracoes",
    [
        {"titulo": "Oi"},
        {"descricao": "curta"},
        {"endereco": ""},
        {"bairro": "   "},
        {"latitude": 91},
        {"longitude": -181},
        {"longitude": None},
        {"latitude": None},
    ],
)
def test_validacoes_de_entrada(cliente, categoria, auth_cidadao, alteracoes):
    resposta = cliente.post(
        URL, json=dados_ocorrencia(categoria.id, **alteracoes), headers=auth_cidadao
    )

    assert resposta.status_code == 422
    assert resposta.json()["erro"]["codigo"] == "DADOS_INVALIDOS"


def test_coordenadas_sao_opcionais(cliente, categoria, auth_cidadao):
    resposta = cliente.post(
        URL,
        json=dados_ocorrencia(categoria.id, latitude=None, longitude=None),
        headers=auth_cidadao,
    )

    assert resposta.status_code == 201
    assert resposta.json()["latitude"] is None


def test_categoria_inexistente_ou_inativa(cliente, db, categoria, auth_cidadao):
    inexistente = cliente.post(URL, json=dados_ocorrencia(999), headers=auth_cidadao)
    categoria.ativa = False
    db.commit()
    inativa = cliente.post(URL, json=dados_ocorrencia(categoria.id), headers=auth_cidadao)

    assert inexistente.status_code == 422
    assert inativa.status_code == 422
    assert inativa.json()["erro"]["codigo"] == "CATEGORIA_INVALIDA"


def test_detalhar_e_publico_e_nao_expoe_email(cliente, nova_ocorrencia):
    ocorrencia = nova_ocorrencia()

    resposta = cliente.get(f"{URL}/{ocorrencia['id']}")

    assert resposta.status_code == 200
    assert resposta.json()["titulo"] == "Buraco grande na rua"
    assert "email" not in resposta.text
    assert "ana@example.com" not in resposta.text


def test_lista_nao_expoe_email(cliente, nova_ocorrencia):
    nova_ocorrencia()

    resposta = cliente.get(URL)

    assert resposta.status_code == 200
    assert "ana@example.com" not in resposta.text


def test_detalhar_inexistente(cliente):
    resposta = cliente.get(f"{URL}/999")

    assert resposta.status_code == 404
    assert resposta.json()["erro"]["codigo"] == "OCORRENCIA_NAO_ENCONTRADA"


def test_lista_mais_recentes_primeiro(cliente, nova_ocorrencia):
    primeira = nova_ocorrencia(titulo="Primeira ocorrência")
    segunda = nova_ocorrencia(titulo="Segunda ocorrência")

    corpo = cliente.get(URL).json()

    assert [item["id"] for item in corpo["itens"]] == [segunda["id"], primeira["id"]]
    assert (corpo["total"], corpo["pagina"], corpo["tamanho"]) == (2, 1, 20)


def test_filtros(cliente, nova_ocorrencia, outra_categoria, mudar_status):
    centro = nova_ocorrencia(bairro="Centro")
    nova_ocorrencia(bairro="Jardim América")
    iluminacao = nova_ocorrencia(bairro="Vila Nova", categoria_id=outra_categoria.id)
    mudar_status(centro["id"], "EM_ANALISE")

    def ids(**params):
        return [item["id"] for item in cliente.get(URL, params=params).json()["itens"]]

    assert ids(bairro="cENTRO") == [centro["id"]]
    assert ids(categoria_id=outra_categoria.id) == [iluminacao["id"]]
    assert ids(status="EM_ANALISE") == [centro["id"]]
    assert ids(bairro="centro", status="ABERTA") == []


def test_filtro_minhas(cliente, nova_ocorrencia, auth_cidadao, auth_outro):
    minha = nova_ocorrencia()
    nova_ocorrencia(auth=auth_outro)

    resposta = cliente.get(URL, params={"minhas": True}, headers=auth_cidadao)

    assert [item["id"] for item in resposta.json()["itens"]] == [minha["id"]]


def test_filtro_minhas_exige_login(cliente):
    resposta = cliente.get(URL, params={"minhas": True})

    assert resposta.status_code == 401


def test_paginacao(cliente, nova_ocorrencia):
    criadas = [nova_ocorrencia(titulo=f"Ocorrência número {i}")["id"] for i in range(5)]

    pagina_2 = cliente.get(URL, params={"pagina": 2, "tamanho": 2}).json()
    pagina_3 = cliente.get(URL, params={"pagina": 3, "tamanho": 2}).json()

    assert [item["id"] for item in pagina_2["itens"]] == [criadas[2], criadas[1]]
    assert [item["id"] for item in pagina_3["itens"]] == [criadas[0]]
    assert (pagina_2["total"], pagina_2["pagina"], pagina_2["tamanho"]) == (5, 2, 2)


@pytest.mark.parametrize("params", [{"tamanho": 101}, {"tamanho": 0}, {"pagina": 0}])
def test_paginacao_fora_dos_limites(cliente, params):
    assert cliente.get(URL, params=params).status_code == 422


def test_dono_altera_ocorrencia_aberta(cliente, categoria, nova_ocorrencia, auth_cidadao):
    ocorrencia = nova_ocorrencia()

    resposta = cliente.put(
        f"{URL}/{ocorrencia['id']}",
        json=dados_ocorrencia(categoria.id, titulo="Título corrigido", bairro="Vila Nova"),
        headers=auth_cidadao,
    )

    assert resposta.status_code == 200
    corpo = resposta.json()
    assert (corpo["titulo"], corpo["bairro"]) == ("Título corrigido", "Vila Nova")
    assert corpo["atualizado_em"] >= ocorrencia["atualizado_em"]


def test_outro_cidadao_nao_altera_nem_exclui(cliente, categoria, nova_ocorrencia, auth_outro):
    ocorrencia = nova_ocorrencia()

    alterar = cliente.put(
        f"{URL}/{ocorrencia['id']}", json=dados_ocorrencia(categoria.id), headers=auth_outro
    )
    excluir = cliente.delete(f"{URL}/{ocorrencia['id']}", headers=auth_outro)

    assert alterar.status_code == 403
    assert excluir.status_code == 403
    assert cliente.get(f"{URL}/{ocorrencia['id']}").status_code == 200


def test_dono_nao_altera_nem_exclui_fora_de_aberta(
    cliente, categoria, nova_ocorrencia, auth_cidadao, mudar_status
):
    ocorrencia = nova_ocorrencia()
    mudar_status(ocorrencia["id"], "EM_ANALISE")

    alterar = cliente.put(
        f"{URL}/{ocorrencia['id']}", json=dados_ocorrencia(categoria.id), headers=auth_cidadao
    )
    excluir = cliente.delete(f"{URL}/{ocorrencia['id']}", headers=auth_cidadao)

    assert alterar.status_code == 403
    assert excluir.status_code == 403


def test_gestor_altera_e_exclui_em_qualquer_status(
    cliente, categoria, nova_ocorrencia, auth_gestor, mudar_status
):
    ocorrencia = nova_ocorrencia()
    mudar_status(ocorrencia["id"], "EM_ANALISE")

    alterar = cliente.put(
        f"{URL}/{ocorrencia['id']}",
        json=dados_ocorrencia(categoria.id, titulo="Ajustado pelo gestor"),
        headers=auth_gestor,
    )
    excluir = cliente.delete(f"{URL}/{ocorrencia['id']}", headers=auth_gestor)

    assert alterar.status_code == 200
    assert alterar.json()["status"] == "EM_ANALISE"
    assert excluir.status_code == 204
    assert cliente.get(f"{URL}/{ocorrencia['id']}").status_code == 404


def test_dono_exclui_ocorrencia_aberta(cliente, nova_ocorrencia, auth_cidadao):
    ocorrencia = nova_ocorrencia()

    resposta = cliente.delete(f"{URL}/{ocorrencia['id']}", headers=auth_cidadao)

    assert resposta.status_code == 204
    assert cliente.get(URL).json()["total"] == 0


def test_alterar_e_excluir_exigem_login(cliente, categoria, nova_ocorrencia):
    ocorrencia = nova_ocorrencia()

    alterar = cliente.put(f"{URL}/{ocorrencia['id']}", json=dados_ocorrencia(categoria.id))
    excluir = cliente.delete(f"{URL}/{ocorrencia['id']}")

    assert alterar.status_code == 401
    assert excluir.status_code == 401
