import pytest

URL = "/api/v1/ocorrencias"

# Caminho (a partir de ABERTA) para chegar em cada status.
CAMINHO = {
    "ABERTA": [],
    "EM_ANALISE": ["EM_ANALISE"],
    "EM_ATENDIMENTO": ["EM_ANALISE", "EM_ATENDIMENTO"],
    "RESOLVIDA": ["EM_ANALISE", "EM_ATENDIMENTO", "RESOLVIDA"],
    "REJEITADA": ["REJEITADA"],
}

VALIDAS = [
    ("ABERTA", "EM_ANALISE"),
    ("EM_ANALISE", "EM_ATENDIMENTO"),
    ("EM_ATENDIMENTO", "RESOLVIDA"),
    ("ABERTA", "REJEITADA"),
    ("EM_ANALISE", "REJEITADA"),
]

INVALIDAS = [
    (origem, destino) for origem in CAMINHO for destino in CAMINHO if (origem, destino) not in VALIDAS
]


@pytest.fixture
def ocorrencia_em(nova_ocorrencia, mudar_status):
    def criar(status: str) -> dict:
        ocorrencia = nova_ocorrencia()
        mudar_status(ocorrencia["id"], *CAMINHO[status], comentario="Preparação do teste")
        return ocorrencia

    return criar


@pytest.mark.parametrize("origem,destino", VALIDAS)
def test_transicoes_validas(cliente, ocorrencia_em, auth_gestor, origem, destino):
    ocorrencia = ocorrencia_em(origem)

    resposta = cliente.patch(
        f"{URL}/{ocorrencia['id']}/status",
        json={"status": destino, "comentario": "Atualização"},
        headers=auth_gestor,
    )

    assert resposta.status_code == 200
    assert resposta.json()["status"] == destino


@pytest.mark.parametrize("origem,destino", INVALIDAS)
def test_transicoes_invalidas(cliente, ocorrencia_em, auth_gestor, origem, destino):
    ocorrencia = ocorrencia_em(origem)

    resposta = cliente.patch(
        f"{URL}/{ocorrencia['id']}/status",
        json={"status": destino, "comentario": "Tentativa"},
        headers=auth_gestor,
    )

    assert resposta.status_code == 409
    erro = resposta.json()["erro"]
    assert erro["codigo"] == "TRANSICAO_INVALIDA"
    assert erro["mensagem"] == f"Não é possível ir de {origem} para {destino}."
    assert cliente.get(f"{URL}/{ocorrencia['id']}").json()["status"] == origem


@pytest.mark.parametrize("comentario", [None, "", "   "])
def test_rejeitar_exige_comentario(cliente, nova_ocorrencia, auth_gestor, comentario):
    ocorrencia = nova_ocorrencia()

    resposta = cliente.patch(
        f"{URL}/{ocorrencia['id']}/status",
        json={"status": "REJEITADA", "comentario": comentario},
        headers=auth_gestor,
    )

    assert resposta.status_code == 422
    assert resposta.json()["erro"]["codigo"] == "COMENTARIO_OBRIGATORIO"
    assert cliente.get(f"{URL}/{ocorrencia['id']}").json()["status"] == "ABERTA"


def test_comentario_e_opcional_nas_demais_transicoes(cliente, nova_ocorrencia, auth_gestor):
    ocorrencia = nova_ocorrencia()

    resposta = cliente.patch(
        f"{URL}/{ocorrencia['id']}/status", json={"status": "EM_ANALISE"}, headers=auth_gestor
    )

    assert resposta.status_code == 200


def test_status_desconhecido(cliente, nova_ocorrencia, auth_gestor):
    ocorrencia = nova_ocorrencia()

    resposta = cliente.patch(
        f"{URL}/{ocorrencia['id']}/status", json={"status": "ARQUIVADA"}, headers=auth_gestor
    )

    assert resposta.status_code == 422


def test_so_gestor_muda_status(cliente, nova_ocorrencia, auth_cidadao):
    ocorrencia = nova_ocorrencia()
    dados = {"status": "EM_ANALISE"}

    como_dono = cliente.patch(f"{URL}/{ocorrencia['id']}/status", json=dados, headers=auth_cidadao)
    sem_login = cliente.patch(f"{URL}/{ocorrencia['id']}/status", json=dados)

    assert como_dono.status_code == 403
    assert sem_login.status_code == 401


def test_ocorrencia_inexistente(cliente, auth_gestor):
    resposta = cliente.patch(
        f"{URL}/999/status", json={"status": "EM_ANALISE"}, headers=auth_gestor
    )

    assert resposta.status_code == 404


def test_historico_registra_criacao_e_mudancas(
    cliente, nova_ocorrencia, cidadao, gestor, auth_gestor
):
    ocorrencia = nova_ocorrencia()
    cliente.patch(
        f"{URL}/{ocorrencia['id']}/status", json={"status": "EM_ANALISE"}, headers=auth_gestor
    )
    cliente.patch(
        f"{URL}/{ocorrencia['id']}/status",
        json={"status": "REJEITADA", "comentario": "Fora da área do município."},
        headers=auth_gestor,
    )

    resposta = cliente.get(f"{URL}/{ocorrencia['id']}/historico")

    assert resposta.status_code == 200
    registros = [
        (r["status_anterior"], r["status_novo"], r["comentario"], r["alterado_por"])
        for r in resposta.json()
    ]
    autor = {"id": cidadao.id, "nome": cidadao.nome}
    responsavel = {"id": gestor.id, "nome": gestor.nome}
    assert registros == [
        (None, "ABERTA", None, autor),
        ("ABERTA", "EM_ANALISE", None, responsavel),
        ("EM_ANALISE", "REJEITADA", "Fora da área do município.", responsavel),
    ]


def test_transicao_invalida_nao_grava_historico(cliente, nova_ocorrencia, auth_gestor):
    ocorrencia = nova_ocorrencia()

    cliente.patch(
        f"{URL}/{ocorrencia['id']}/status", json={"status": "RESOLVIDA"}, headers=auth_gestor
    )

    assert len(cliente.get(f"{URL}/{ocorrencia['id']}/historico").json()) == 1


def test_historico_de_ocorrencia_inexistente(cliente):
    assert cliente.get(f"{URL}/999/historico").status_code == 404


def test_resolvido_em_so_e_preenchido_ao_resolver(cliente, nova_ocorrencia, mudar_status):
    ocorrencia = nova_ocorrencia()

    em_atendimento = mudar_status(ocorrencia["id"], "EM_ANALISE", "EM_ATENDIMENTO").json()
    resolvida = mudar_status(ocorrencia["id"], "RESOLVIDA").json()

    assert em_atendimento["resolvido_em"] is None
    assert resolvida["resolvido_em"] is not None
    assert resolvida["resolvido_em"] >= resolvida["criado_em"]


def test_rejeitada_nao_preenche_resolvido_em(cliente, nova_ocorrencia, mudar_status):
    ocorrencia = nova_ocorrencia()

    rejeitada = mudar_status(ocorrencia["id"], "REJEITADA", comentario="Duplicada").json()

    assert rejeitada["status"] == "REJEITADA"
    assert rejeitada["resolvido_em"] is None


def test_mudancas_simultaneas_nao_duplicam_o_historico(nova_ocorrencia, gestor):
    """Dois gestores movendo a mesma ocorrência ao mesmo tempo: só um deve conseguir."""
    from concurrent.futures import ThreadPoolExecutor

    from app.core.excecoes import Conflito
    from app.db.sessao import SessaoLocal
    from app.models import HistoricoStatus, StatusOcorrencia
    from app.schemas.ocorrencia import StatusEntrada
    from app.services.armazenamento import ArmazenamentoFotosDisco
    from app.services.ocorrencia import OcorrenciaServico

    ocorrencia_id = nova_ocorrencia()["id"]

    def mudar(_):
        with SessaoLocal() as db:
            servico = OcorrenciaServico(db, ArmazenamentoFotosDisco("uploads"))
            try:
                servico.mudar_status(ocorrencia_id, StatusEntrada(status=StatusOcorrencia.EM_ANALISE), db.merge(gestor))
                return "ok"
            except Conflito:
                return "conflito"

    with ThreadPoolExecutor(max_workers=8) as executor:
        resultados = list(executor.map(mudar, range(8)))

    assert resultados.count("ok") == 1
    assert resultados.count("conflito") == 7
    with SessaoLocal() as db:
        assert db.query(HistoricoStatus).filter_by(ocorrencia_id=ocorrencia_id).count() == 2
