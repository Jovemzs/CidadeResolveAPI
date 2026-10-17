def test_listar_e_detalhar_sao_publicos(cliente, categoria):
    lista = cliente.get("/api/v1/categorias")
    detalhe = cliente.get(f"/api/v1/categorias/{categoria.id}")

    assert lista.status_code == 200
    assert [item["nome"] for item in lista.json()] == ["Buraco na via"]
    assert detalhe.status_code == 200
    assert detalhe.json()["descricao"] == "Buracos no asfalto"


def test_detalhar_inexistente(cliente):
    resposta = cliente.get("/api/v1/categorias/999")

    assert resposta.status_code == 404
    assert resposta.json()["erro"]["codigo"] == "CATEGORIA_NAO_ENCONTRADA"


def test_gestor_cria_categoria(cliente, auth_gestor):
    resposta = cliente.post(
        "/api/v1/categorias",
        json={"nome": "Poda de árvore", "descricao": "Galhos sobre a via"},
        headers=auth_gestor,
    )

    assert resposta.status_code == 201
    assert resposta.json()["nome"] == "Poda de árvore"
    assert resposta.json()["ativa"] is True


def test_nome_duplicado(cliente, categoria, auth_gestor):
    resposta = cliente.post(
        "/api/v1/categorias", json={"nome": "buraco na VIA"}, headers=auth_gestor
    )

    assert resposta.status_code == 409
    assert resposta.json()["erro"]["codigo"] == "CATEGORIA_DUPLICADA"


def test_gestor_altera_categoria(cliente, categoria, auth_gestor):
    resposta = cliente.put(
        f"/api/v1/categorias/{categoria.id}",
        json={"nome": "Buraco", "descricao": None, "ativa": False},
        headers=auth_gestor,
    )

    assert resposta.status_code == 200
    assert resposta.json() == {
        "id": categoria.id,
        "nome": "Buraco",
        "descricao": None,
        "ativa": False,
    }


def test_lista_so_ativas_por_padrao(cliente, categoria, outra_categoria, auth_gestor):
    cliente.put(
        f"/api/v1/categorias/{categoria.id}",
        json={"nome": categoria.nome, "ativa": False},
        headers=auth_gestor,
    )

    ativas = cliente.get("/api/v1/categorias").json()
    todas = cliente.get("/api/v1/categorias", params={"incluir_inativas": True}).json()

    assert [item["nome"] for item in ativas] == ["Iluminação pública"]
    assert len(todas) == 2


def test_gestor_exclui_categoria_sem_ocorrencias(cliente, categoria, auth_gestor):
    resposta = cliente.delete(f"/api/v1/categorias/{categoria.id}", headers=auth_gestor)

    assert resposta.status_code == 204
    assert cliente.get(f"/api/v1/categorias/{categoria.id}").status_code == 404


def test_nao_exclui_categoria_em_uso(cliente, categoria, auth_gestor, nova_ocorrencia):
    nova_ocorrencia()

    resposta = cliente.delete(f"/api/v1/categorias/{categoria.id}", headers=auth_gestor)

    assert resposta.status_code == 409
    assert resposta.json()["erro"]["codigo"] == "CATEGORIA_EM_USO"
    assert cliente.get(f"/api/v1/categorias/{categoria.id}").status_code == 200


def test_cidadao_nao_gerencia_categorias(cliente, categoria, auth_cidadao):
    dados = {"nome": "Nova categoria"}

    criar = cliente.post("/api/v1/categorias", json=dados, headers=auth_cidadao)
    alterar = cliente.put(f"/api/v1/categorias/{categoria.id}", json=dados, headers=auth_cidadao)
    excluir = cliente.delete(f"/api/v1/categorias/{categoria.id}", headers=auth_cidadao)

    assert [criar.status_code, alterar.status_code, excluir.status_code] == [403, 403, 403]
    assert criar.json()["erro"]["codigo"] == "SEM_PERMISSAO"


def test_publico_nao_gerencia_categorias(cliente, categoria):
    dados = {"nome": "Nova categoria"}

    criar = cliente.post("/api/v1/categorias", json=dados)
    alterar = cliente.put(f"/api/v1/categorias/{categoria.id}", json=dados)
    excluir = cliente.delete(f"/api/v1/categorias/{categoria.id}")

    assert [criar.status_code, alterar.status_code, excluir.status_code] == [401, 401, 401]
