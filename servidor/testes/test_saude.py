from fastapi.testclient import TestClient

from app import __version__
from app.principal import app

cliente = TestClient(app)


def test_rota_de_saude_responde_ok():
    resposta = cliente.get("/api/saude")

    assert resposta.status_code == 200
    assert resposta.json() == {"status": "ok", "versao": __version__}
