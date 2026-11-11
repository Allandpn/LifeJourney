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


def test_migracao_mantem_os_dados_de_um_banco_da_versao_anterior(tmp_path):
    """Como no Pi ao atualizar: banco com dados na primeira versão, depois as migrações novas."""
    from alembic import command
    from alembic.config import Config
    from sqlalchemy import text

    from app.banco import PASTA_DO_SERVIDOR, criar_motor, preparar_banco

    motor = criar_motor(f"sqlite:///{tmp_path / 'antigo.db'}")
    config = Config(str(PASTA_DO_SERVIDOR / "alembic.ini"))
    config.set_main_option("script_location", str(PASTA_DO_SERVIDOR / "migracoes"))
    config.set_main_option("version_locations", str(PASTA_DO_SERVIDOR / "migracoes" / "versoes"))
    with motor.begin() as conexao:
        config.attributes["conexao"] = conexao
        command.upgrade(config, "0035e3a3bf29")  # primeira versão
        conexao.execute(text("insert into usuario (id, email, administrador, criado_em) values ('u', 'u@x.y', 0, '2026-01-01')"))
        conexao.execute(text("insert into memoria (id, usuario_id, criado_em, atualizado_em, data, texto, intensidade, "
                             "marcante, silenciar, veio_de, tags) values ('m', 'u', '2026-01-01', '2026-01-01', "
                             "'2020-01-01', 'Antes da migração.', 2, 0, 0, '[]', '[]')"))

    preparar_banco(motor)

    with motor.connect() as c:
        assert c.execute(text("select texto, id_de_origem from memoria")).one() == ("Antes da migração.", None)


def test_origem_permitida_por_configuracao(servidor, monkeypatch):
    """Atrás do Tailscale o endereço do pedido pode mudar; o endereço público configurado vale como origem."""
    from app import principal
    from app.config import Configuracao
    from conftest import entrar

    cliente = entrar(servidor())
    pedido = {"data": "2020-01-01", "texto": "x"}
    origem = {"Origin": "https://pi.exemplo.ts.net"}
    assert cliente.post("/api/memorias", json=pedido, headers=origem).status_code == 403

    config = Configuracao(modo="desenvolvimento", caminho_banco=None, pasta_fotos=None, email_desenvolvimento="x",
                          origens_permitidas=("pi.exemplo.ts.net",))
    monkeypatch.setattr(principal, "obter_configuracao", lambda: config)
    assert cliente.post("/api/memorias", json=pedido, headers=origem).status_code == 201
    assert cliente.post("/api/memorias", json=pedido, headers={"Origin": "https://malicioso.example"}).status_code == 403
