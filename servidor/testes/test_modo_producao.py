"""Sem login, nada é devolvido, em qualquer modo."""

from fastapi.testclient import TestClient

from app.principal import app


def test_sem_login_as_rotas_de_dados_recusam():
    cliente = TestClient(app)
    for rota in ("/api/memorias", "/api/capitulos", "/api/intencoes", "/api/perfil", "/api/estimativa", "/api/conta"):
        assert cliente.get(rota).status_code == 401, rota
