def test_site_e_servido_na_raiz(cliente):
    resposta = cliente.get("/")

    assert resposta.status_code == 200
    assert resposta.headers["content-type"].startswith("text/html")
    assert "CidadeResolve" in resposta.text


def test_arquivos_do_site(cliente):
    for caminho in ("/estilo.css", "/js/app.js", "/js/paginas/lista.js", "/favicon.svg"):
        assert cliente.get(caminho).status_code == 200, caminho


def test_site_nao_encobre_a_api_nem_o_swagger(cliente):
    assert cliente.get("/docs").status_code == 200
    assert cliente.get("/saude").json() == {"status": "ok"}
    assert cliente.get("/api/v1/categorias").status_code == 200
    assert cliente.get("/api/v1/nao-existe").json()["erro"]["codigo"] == "NAO_ENCONTRADO"


def test_mensagens_de_validacao_em_portugues(cliente):
    resposta = cliente.post(
        "/api/v1/auth/registro", json={"nome": "A", "email": "nao-e-email", "senha": "123"}
    )

    mensagens = {d["campo"]: d["mensagem"] for d in resposta.json()["erro"]["detalhes"]}
    assert mensagens == {
        "nome": "Deve ter pelo menos 2 caractere(s).",
        "email": "Informe um e-mail válido.",
        "senha": "Deve ter pelo menos 8 caractere(s).",
    }


def test_mensagem_de_regra_propria_e_preservada(cliente, categoria, auth_cidadao):
    resposta = cliente.post(
        "/api/v1/ocorrencias",
        json={
            "titulo": "Buraco grande",
            "descricao": "Buraco fundo em frente ao 120.",
            "categoria_id": categoria.id,
            "endereco": "Rua A, 1",
            "bairro": "Centro",
            "latitude": -23.5,
        },
        headers=auth_cidadao,
    )

    assert resposta.json()["erro"]["detalhes"][0]["mensagem"] == (
        "Latitude e longitude devem ser informadas juntas."
    )


def test_campo_nulo_vira_campo_obrigatorio(cliente, auth_cidadao):
    resposta = cliente.post(
        "/api/v1/ocorrencias",
        json={"titulo": "", "descricao": "", "categoria_id": None, "endereco": "", "bairro": ""},
        headers=auth_cidadao,
    )

    mensagens = {d["campo"]: d["mensagem"] for d in resposta.json()["erro"]["detalhes"]}
    assert mensagens["categoria_id"] == "Campo obrigatório."
    assert set(mensagens) == {"titulo", "descricao", "categoria_id", "endereco", "bairro"}
