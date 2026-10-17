from app.core.config import obter_configuracoes
from app.models import Categoria, Papel, Usuario
from app.seed import executar_carga


def test_carga_inicial_e_idempotente(db, cliente, monkeypatch):
    config = obter_configuracoes()
    monkeypatch.setattr(config, "gestor_email", "Gestor@Example.com")
    monkeypatch.setattr(config, "gestor_senha", "senha-do-gestor")

    executar_carga(db)
    executar_carga(db)

    gestores = db.query(Usuario).all()
    assert [(g.email, g.papel) for g in gestores] == [("gestor@example.com", Papel.GESTOR)]
    assert sorted(c.nome for c in db.query(Categoria).all()) == [
        "Buraco na via",
        "Descarte irregular de lixo",
        "Iluminação pública",
    ]
    login = cliente.post(
        "/api/v1/auth/login", json={"email": "gestor@example.com", "senha": "senha-do-gestor"}
    )
    assert login.status_code == 200
