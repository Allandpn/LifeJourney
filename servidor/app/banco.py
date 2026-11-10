"""Conexão com o banco de dados (SQLite)."""

from __future__ import annotations

from collections.abc import Iterator

from sqlalchemy import event
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


def criar_tabelas(motor: Engine) -> None:
    """Cria as tabelas que ainda não existem. Não altera tabelas já existentes."""
    SQLModel.metadata.create_all(motor)


def obter_sessao() -> Iterator[Session]:
    """Dependência do FastAPI: uma sessão de banco por requisição."""
    with Session(obter_motor()) as sessao:
        yield sessao
