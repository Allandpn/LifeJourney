"""Enquanto não há login, o servidor em modo produção recusa tudo."""

from fastapi.testclient import TestClient

from app.config import Configuracao, obter_configuracao
from app.principal import app


def test_producao_sem_login_recusa_requisicoes(tmp_path):
    app.dependency_overrides[obter_configuracao] = lambda: Configuracao(
        modo="producao", caminho_banco=tmp_path / "x.db", email_desenvolvimento="dev@exemplo.local"
    )
    try:
        assert TestClient(app).get("/api/memorias").status_code == 401
    finally:
        app.dependency_overrides.clear()
