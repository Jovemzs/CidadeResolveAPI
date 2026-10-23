"""Teste de performance (carga) da CidadeResolve API com Locust.

Simula três perfis ao mesmo tempo: visitantes consultando ocorrências, cidadãos
registrando problemas e gestores atualizando o andamento.

Como rodar (com a API ligada em http://localhost:8000):

    locust -f tests/performance/locustfile.py --host http://localhost:8000 \
        --headless -u 50 -r 5 -t 90s --html docs/performance/relatorio.html

Sem --headless, abre um painel em http://localhost:8089 para acompanhar ao vivo.
"""

import os
import random
import uuid

from locust import HttpUser, between, task

BAIRROS = ["Centro", "Mooca", "Brás", "Belém", "Consolação", "Vila Mariana"]
GESTOR_EMAIL = os.environ.get("GESTOR_EMAIL", "gestor@cidaderesolve.com")
GESTOR_SENHA = os.environ.get("GESTOR_SENHA", "gestor12345")


class Visitante(HttpUser):
    """Pessoa sem login navegando pelas ocorrências públicas."""

    weight = 6
    wait_time = between(1, 3)

    def on_start(self):
        categorias = self.client.get("/api/v1/categorias").json()
        self.categorias = [c["id"] for c in categorias] or [1]
        self.ids = []

    @task(5)
    def listar_ocorrencias(self):
        resposta = self.client.get("/api/v1/ocorrencias", params={"tamanho": 10})
        if resposta.ok:
            self.ids = [o["id"] for o in resposta.json()["itens"]]

    @task(2)
    def filtrar_por_bairro(self):
        self.client.get(
            "/api/v1/ocorrencias",
            params={"bairro": random.choice(BAIRROS), "categoria_id": random.choice(self.categorias)},
            name="/api/v1/ocorrencias?bairro&categoria_id",
        )

    @task(3)
    def detalhar_ocorrencia(self):
        if self.ids:
            self.client.get(f"/api/v1/ocorrencias/{random.choice(self.ids)}", name="/api/v1/ocorrencias/{id}")

    @task(1)
    def ver_historico(self):
        if self.ids:
            self.client.get(
                f"/api/v1/ocorrencias/{random.choice(self.ids)}/historico",
                name="/api/v1/ocorrencias/{id}/historico",
            )

    @task(1)
    def listar_categorias(self):
        self.client.get("/api/v1/categorias")


class Cidadao(HttpUser):
    """Cidadão que cria a conta, entra e registra ocorrências."""

    weight = 3
    wait_time = between(2, 5)

    def on_start(self):
        email = f"carga.{uuid.uuid4().hex[:12]}@example.com"
        self.client.post("/api/v1/auth/registro", json={"nome": "Usuário de carga", "email": email, "senha": "senha12345"})
        token = self.client.post("/api/v1/auth/login", json={"email": email, "senha": "senha12345"}).json()["access_token"]
        self.client.headers["Authorization"] = f"Bearer {token}"
        self.categorias = [c["id"] for c in self.client.get("/api/v1/categorias").json()] or [1]

    @task(2)
    def registrar_ocorrencia(self):
        self.client.post(
            "/api/v1/ocorrencias",
            json={
                "titulo": "Ocorrência do teste de carga",
                "descricao": "Registro automático criado pelo teste de performance.",
                "categoria_id": random.choice(self.categorias),
                "endereco": f"Rua de Teste, {random.randint(1, 999)}",
                "bairro": random.choice(BAIRROS),
                "latitude": -23.55 + random.uniform(-0.05, 0.05),
                "longitude": -46.63 + random.uniform(-0.05, 0.05),
            },
        )

    @task(3)
    def ver_minhas(self):
        self.client.get("/api/v1/ocorrencias", params={"minhas": True}, name="/api/v1/ocorrencias?minhas")

    @task(1)
    def ver_perfil(self):
        self.client.get("/api/v1/auth/eu")


class Gestor(HttpUser):
    """Gestor que acompanha os indicadores e move ocorrências abertas para análise."""

    weight = 1
    wait_time = between(2, 5)

    def on_start(self):
        token = self.client.post("/api/v1/auth/login", json={"email": GESTOR_EMAIL, "senha": GESTOR_SENHA}).json()["access_token"]
        self.client.headers["Authorization"] = f"Bearer {token}"

    @task(2)
    def ver_indicadores(self):
        self.client.get("/api/v1/indicadores")

    @task(1)
    def analisar_aberta(self):
        abertas = self.client.get(
            "/api/v1/ocorrencias", params={"status": "ABERTA", "tamanho": 5}, name="/api/v1/ocorrencias?status"
        ).json()["itens"]
        if abertas:
            self.client.patch(
                f"/api/v1/ocorrencias/{abertas[0]['id']}/status",
                json={"status": "EM_ANALISE", "comentario": "Triagem do teste de carga."},
                name="/api/v1/ocorrencias/{id}/status",
            )
