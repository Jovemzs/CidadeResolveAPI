REGISTRO = {"nome": "Ana Cidadã", "email": "ana@example.com", "senha": "senha12345"}


def test_registro_cria_cidadao(cliente):
    resposta = cliente.post("/api/v1/auth/registro", json=REGISTRO)

    assert resposta.status_code == 201
    corpo = resposta.json()
    assert corpo["email"] == "ana@example.com"
    assert corpo["papel"] == "CIDADAO"
    assert "senha" not in corpo and "senha_hash" not in corpo


def test_registro_ignora_papel_enviado(cliente):
    resposta = cliente.post("/api/v1/auth/registro", json={**REGISTRO, "papel": "GESTOR"})

    assert resposta.status_code == 201
    assert resposta.json()["papel"] == "CIDADAO"


def test_registro_email_duplicado(cliente):
    cliente.post("/api/v1/auth/registro", json=REGISTRO)

    resposta = cliente.post("/api/v1/auth/registro", json={**REGISTRO, "email": "ANA@example.com"})

    assert resposta.status_code == 409
    assert resposta.json()["erro"]["codigo"] == "EMAIL_JA_CADASTRADO"


def test_registro_dados_invalidos(cliente):
    resposta = cliente.post(
        "/api/v1/auth/registro", json={"nome": "A", "email": "nao-e-email", "senha": "123"}
    )

    assert resposta.status_code == 422
    erro = resposta.json()["erro"]
    assert erro["codigo"] == "DADOS_INVALIDOS"
    assert {detalhe["campo"] for detalhe in erro["detalhes"]} == {"nome", "email", "senha"}


def test_login_valido_devolve_token_utilizavel(cliente):
    cliente.post("/api/v1/auth/registro", json=REGISTRO)

    resposta = cliente.post(
        "/api/v1/auth/login", json={"email": REGISTRO["email"], "senha": REGISTRO["senha"]}
    )

    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["token_type"] == "bearer"
    eu = cliente.get("/api/v1/auth/eu", headers={"Authorization": f"Bearer {corpo['access_token']}"})
    assert eu.status_code == 200
    assert eu.json()["email"] == "ana@example.com"


def test_login_senha_errada(cliente):
    cliente.post("/api/v1/auth/registro", json=REGISTRO)

    resposta = cliente.post(
        "/api/v1/auth/login", json={"email": REGISTRO["email"], "senha": "senha-errada"}
    )

    assert resposta.status_code == 401
    assert resposta.json()["erro"]["codigo"] == "CREDENCIAIS_INVALIDAS"


def test_login_usuario_inexistente(cliente):
    resposta = cliente.post(
        "/api/v1/auth/login", json={"email": "ninguem@example.com", "senha": "senha12345"}
    )

    assert resposta.status_code == 401


def test_rota_protegida_sem_token(cliente):
    resposta = cliente.get("/api/v1/auth/eu")

    assert resposta.status_code == 401
    assert resposta.json()["erro"]["codigo"] == "NAO_AUTENTICADO"


def test_rota_protegida_com_token_invalido(cliente):
    resposta = cliente.get("/api/v1/auth/eu", headers={"Authorization": "Bearer token-falso"})

    assert resposta.status_code == 401
    assert resposta.json()["erro"]["codigo"] == "TOKEN_INVALIDO"


def test_rota_inexistente_usa_formato_unico_de_erro(cliente):
    resposta = cliente.get("/api/v1/nao-existe")

    assert resposta.status_code == 404
    assert set(resposta.json()["erro"]) == {"codigo", "mensagem"}


def test_cors_libera_o_front_end_local(cliente):
    resposta = cliente.options(
        "/api/v1/ocorrencias",
        headers={"Origin": "http://localhost:5173", "Access-Control-Request-Method": "POST"},
    )

    assert resposta.status_code == 200
    assert resposta.headers["access-control-allow-origin"] == "http://localhost:5173"


def test_cors_bloqueia_origem_desconhecida(cliente):
    resposta = cliente.get("/api/v1/categorias", headers={"Origin": "https://site-qualquer.com"})

    assert "access-control-allow-origin" not in resposta.headers
