from datetime import datetime, timedelta, timezone

import pytest

from app.models import Ocorrencia, StatusOcorrencia

URL = "/api/v1/indicadores"


def utc(dia: int, hora: int = 12) -> datetime:
    return datetime(2026, 3, dia, hora, tzinfo=timezone.utc)


@pytest.fixture
def conjunto_conhecido(db, cidadao, categoria, outra_categoria):
    """Seis ocorrências com datas, status, categorias e bairros definidos.

    Resolvidas: uma em 10 h e outra em 20 h (média 15 h).
    """

    def ocorrencia(dia, status, categoria_usada, bairro, horas_para_resolver=None):
        criado_em = utc(dia)
        return Ocorrencia(
            titulo="Ocorrência de teste",
            descricao="Descrição da ocorrência de teste.",
            categoria_id=categoria_usada.id,
            autor_id=cidadao.id,
            status=status,
            endereco="Rua A, 1",
            bairro=bairro,
            criado_em=criado_em,
            resolvido_em=(
                criado_em + timedelta(hours=horas_para_resolver) if horas_para_resolver else None
            ),
        )

    db.add_all(
        [
            ocorrencia(1, StatusOcorrencia.RESOLVIDA, categoria, "Centro", 10),
            ocorrencia(2, StatusOcorrencia.RESOLVIDA, categoria, "Centro", 20),
            ocorrencia(3, StatusOcorrencia.ABERTA, categoria, "Centro"),
            ocorrencia(10, StatusOcorrencia.EM_ANALISE, outra_categoria, "Vila Nova"),
            ocorrencia(11, StatusOcorrencia.REJEITADA, outra_categoria, "Vila Nova"),
            ocorrencia(20, StatusOcorrencia.EM_ATENDIMENTO, categoria, "Jardim América"),
        ]
    )
    db.commit()


def test_indicadores_do_conjunto_conhecido(
    cliente, conjunto_conhecido, categoria, outra_categoria, auth_gestor
):
    resposta = cliente.get(URL, headers=auth_gestor)

    assert resposta.status_code == 200
    assert resposta.json() == {
        "total_ocorrencias": 6,
        "por_status": {
            "ABERTA": 1,
            "EM_ANALISE": 1,
            "EM_ATENDIMENTO": 1,
            "RESOLVIDA": 2,
            "REJEITADA": 1,
        },
        "por_categoria": [
            {"categoria_id": categoria.id, "nome": "Buraco na via", "quantidade": 4},
            {"categoria_id": outra_categoria.id, "nome": "Iluminação pública", "quantidade": 2},
        ],
        "por_bairro": [
            {"bairro": "Centro", "quantidade": 3},
            {"bairro": "Vila Nova", "quantidade": 2},
            {"bairro": "Jardim América", "quantidade": 1},
        ],
        "taxa_resolucao": 33.33,
        "tempo_medio_resolucao_horas": 15.0,
    }


def test_filtro_por_periodo(cliente, conjunto_conhecido, auth_gestor):
    # Dias 2 a 10, inclusive nas duas pontas: uma resolvida (20 h), uma aberta, uma em análise.
    resposta = cliente.get(
        URL, params={"data_inicio": "2026-03-02", "data_fim": "2026-03-10"}, headers=auth_gestor
    )

    corpo = resposta.json()
    assert corpo["total_ocorrencias"] == 3
    assert corpo["por_status"]["RESOLVIDA"] == 1
    assert corpo["por_bairro"] == [
        {"bairro": "Centro", "quantidade": 2},
        {"bairro": "Vila Nova", "quantidade": 1},
    ]
    assert corpo["taxa_resolucao"] == 33.33
    assert corpo["tempo_medio_resolucao_horas"] == 20.0


def test_so_data_inicio(cliente, conjunto_conhecido, auth_gestor):
    corpo = cliente.get(URL, params={"data_inicio": "2026-03-11"}, headers=auth_gestor).json()

    assert corpo["total_ocorrencias"] == 2
    assert corpo["taxa_resolucao"] == 0.0
    assert corpo["tempo_medio_resolucao_horas"] is None


def test_sem_ocorrencias(cliente, auth_gestor):
    corpo = cliente.get(URL, headers=auth_gestor).json()

    assert corpo["total_ocorrencias"] == 0
    assert corpo["por_status"] == {
        "ABERTA": 0,
        "EM_ANALISE": 0,
        "EM_ATENDIMENTO": 0,
        "RESOLVIDA": 0,
        "REJEITADA": 0,
    }
    assert corpo["por_categoria"] == []
    assert corpo["por_bairro"] == []
    assert corpo["taxa_resolucao"] == 0.0
    assert corpo["tempo_medio_resolucao_horas"] is None


def test_periodo_invertido(cliente, auth_gestor):
    resposta = cliente.get(
        URL, params={"data_inicio": "2026-03-10", "data_fim": "2026-03-01"}, headers=auth_gestor
    )

    assert resposta.status_code == 422
    assert resposta.json()["erro"]["codigo"] == "PERIODO_INVALIDO"


def test_acesso_restrito_a_gestores(cliente, auth_cidadao):
    assert cliente.get(URL).status_code == 401
    assert cliente.get(URL, headers=auth_cidadao).status_code == 403


def test_indicadores_refletem_o_fluxo_pela_api(cliente, nova_ocorrencia, mudar_status, auth_gestor):
    resolvida = nova_ocorrencia()
    nova_ocorrencia()
    mudar_status(resolvida["id"], "EM_ANALISE", "EM_ATENDIMENTO", "RESOLVIDA")

    corpo = cliente.get(URL, headers=auth_gestor).json()

    assert corpo["total_ocorrencias"] == 2
    assert corpo["taxa_resolucao"] == 50.0
    assert corpo["tempo_medio_resolucao_horas"] is not None
    assert corpo["tempo_medio_resolucao_horas"] >= 0
