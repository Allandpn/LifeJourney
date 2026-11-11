"""Ambiente do Alembic: usa as tabelas de app/modelos.py e o banco configurado."""

from alembic import context
from sqlmodel import SQLModel

from app import modelos  # noqa: F401  (registra as tabelas)
from app.banco import criar_motor
from app.config import obter_configuracao

alvo = SQLModel.metadata


def rodar() -> None:
    conexao = context.config.attributes.get("conexao")
    if conexao is not None:
        context.configure(connection=conexao, target_metadata=alvo, render_as_batch=True)
        with context.begin_transaction():
            context.run_migrations()
        return
    motor = criar_motor(f"sqlite:///{obter_configuracao().caminho_banco}")
    with motor.connect() as conexao:
        context.configure(connection=conexao, target_metadata=alvo, render_as_batch=True)
        with context.begin_transaction():
            context.run_migrations()


rodar()
