"""Peças da publicação: endereço real atrás do túnel, página do aplicativo, migrações."""

import importlib

import pytest
from fastapi.testclient import TestClient

from conftest import SENHA_ANA


def test_limite_por_endereco_usa_o_cabecalho_do_tunel(servidor, monkeypatch):
    from app.api import contas
    from app.config import Configuracao

    config = Configuracao(modo="desenvolvimento", caminho_banco=None, pasta_fotos=None,
                          email_desenvolvimento="x", cabecalho_do_ip="CF-Connecting-IP")
    monkeypatch.setattr(contas, "obter_configuracao", lambda: config)
    cliente = servidor()
    # 20 erros vindos de um endereço bloqueiam esse endereço, mas não outro
    for i in range(20):
        cliente.post("/api/entrar", json={"email": f"x{i}@exemplo.local", "senha": "errada-123456"},
                     headers={"CF-Connecting-IP": "203.0.113.7"})
    bloqueado = cliente.post("/api/entrar", json={"email": "ana@exemplo.local", "senha": SENHA_ANA},
                             headers={"CF-Connecting-IP": "203.0.113.7"})
    outro = cliente.post("/api/entrar", json={"email": "ana@exemplo.local", "senha": SENHA_ANA},
                         headers={"CF-Connecting-IP": "198.51.100.9"})
    assert bloqueado.status_code == 429 and outro.status_code == 200


def test_login_apaga_sessoes_vencidas(servidor):
    from datetime import timedelta

    from sqlmodel import Session, select

    from app.modelos import Sessao, agora
    from conftest import entrar

    entrar(servidor())
    with Session(servidor.motor) as s:
        for x in s.exec(select(Sessao)):
            x.expira_em = agora() - timedelta(days=1)
            s.add(x)
        s.commit()
    entrar(servidor())
    with Session(servidor.motor) as s:
        assert len(s.exec(select(Sessao)).all()) == 1


@pytest.fixture
def com_aplicativo(tmp_path, monkeypatch):
    """Recarrega o servidor em modo produção, servindo um aplicativo compilado de mentira."""
    (tmp_path / "assets").mkdir()
    (tmp_path / "index.html").write_text("<!doctype html><title>Vida em Semanas</title>")
    (tmp_path / "assets" / "index-abc123.js").write_text("console.log(1)")
    monkeypatch.setenv("LJ_APLICATIVO", str(tmp_path))
    monkeypatch.setenv("LJ_MODO", "producao")
    from app import config, principal

    config.obter_configuracao.cache_clear()
    yield importlib.reload(principal).app
    monkeypatch.delenv("LJ_APLICATIVO")
    monkeypatch.delenv("LJ_MODO")
    config.obter_configuracao.cache_clear()
    importlib.reload(principal)


def test_serve_a_pagina_com_politica_de_conteudo(com_aplicativo):
    cliente = TestClient(com_aplicativo)
    pagina = cliente.get("/")
    assert pagina.status_code == 200 and "Vida em Semanas" in pagina.text
    politica = pagina.headers["content-security-policy"]
    assert "script-src 'self'" in politica and "frame-ancestors 'none'" in politica
    assert pagina.headers["cache-control"] == "no-cache"
    assert pagina.headers["strict-transport-security"].startswith("max-age=")
    arquivo = cliente.get("/assets/index-abc123.js")
    assert "immutable" in arquivo.headers["cache-control"]


def test_em_producao_a_api_continua_e_a_documentacao_some(com_aplicativo):
    cliente = TestClient(com_aplicativo)
    assert cliente.get("/api/saude").json()["status"] == "ok"
    assert cliente.get("/api/memorias").status_code == 401
    assert cliente.get("/docs").status_code == 404
    assert cliente.get("/openapi.json").status_code == 404


def test_migracoes_criam_o_mesmo_banco_que_os_modelos(tmp_path):
    from alembic.autogenerate import compare_metadata
    from alembic.migration import MigrationContext
    from sqlalchemy import inspect
    from sqlmodel import SQLModel

    from app.banco import criar_motor, preparar_banco

    motor = criar_motor(f"sqlite:///{tmp_path / 'novo.db'}")
    preparar_banco(motor)
    assert "alembic_version" in inspect(motor).get_table_names()
    with motor.connect() as conexao:
        assert compare_metadata(MigrationContext.configure(conexao), SQLModel.metadata) == []
    preparar_banco(motor)  # rodar de novo não faz nada


def test_banco_antigo_sem_migracoes_e_marcado_na_versao_atual(tmp_path):
    from sqlalchemy import inspect, text

    from app.banco import criar_motor, criar_tabelas, preparar_banco

    motor = criar_motor(f"sqlite:///{tmp_path / 'antigo.db'}")
    criar_tabelas(motor)
    preparar_banco(motor)
    assert "alembic_version" in inspect(motor).get_table_names()
    with motor.connect() as c:
        assert c.execute(text("select count(*) from alembic_version")).scalar() == 1
