"""Conexão com o banco de dados (SQLite)."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

from sqlalchemy import event, inspect
from sqlalchemy.engine import Engine
from sqlmodel import Session, SQLModel, create_engine

from app import modelos  # noqa: F401  (registra as tabelas no SQLModel)
from app.config import obter_configuracao

_motor: Engine | None = None


def criar_motor(url: str, **opcoes) -> Engine:
    motor = create_engine(url, connect_args={"check_same_thread": False}, **opcoes)

    # O SQLite só respeita chaves estrangeiras com esta opção ligada.
    @event.listens_for(motor, "connect")
    def _ligar_chaves_estrangeiras(conexao, _registro):
        conexao.execute("PRAGMA foreign_keys = ON")

    return motor


def obter_motor() -> Engine:
    """Motor do banco configurado em LJ_BANCO, criado na primeira chamada."""
    global _motor
    if _motor is None:
        caminho = obter_configuracao().caminho_banco
        caminho.parent.mkdir(parents=True, exist_ok=True)
        _motor = criar_motor(f"sqlite:///{caminho}")
    return _motor


PASTA_DO_SERVIDOR = Path(__file__).resolve().parents[1]


def criar_tabelas(motor: Engine) -> None:
    """Cria as tabelas direto dos modelos, sem migrações. Usado nos testes."""
    SQLModel.metadata.create_all(motor)


def preparar_banco(motor: Engine) -> None:
    """Deixa o banco com a estrutura mais recente, aplicando as migrações que faltam.

    Um banco criado antes de existirem migrações (só em desenvolvimento) é marcado
    como estando na versão atual.
    """
    from alembic import command
    from alembic.config import Config

    config = Config(str(PASTA_DO_SERVIDOR / "alembic.ini"))
    config.set_main_option("script_location", str(PASTA_DO_SERVIDOR / "migracoes"))
    config.set_main_option("version_locations", str(PASTA_DO_SERVIDOR / "migracoes" / "versoes"))
    tabelas = set(inspect(motor).get_table_names())
    with motor.begin() as conexao:
        config.attributes["conexao"] = conexao
        if tabelas and "alembic_version" not in tabelas:
            command.stamp(config, "head")
        else:
            command.upgrade(config, "head")


def obter_sessao() -> Iterator[Session]:
    """Dependência do FastAPI: uma sessão de banco por requisição."""
    with Session(obter_motor()) as sessao:
        yield sessao
