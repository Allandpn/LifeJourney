"""Tabelas do banco de dados (docs/04-modelo-de-dados.md).

Toda tabela de conteúdo tem um dono (`usuario_id`) e é apagada só por marcação
(`excluido_em`), para os outros aparelhos saberem da exclusão ao sincronizar.
"""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime
from typing import Any

from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel


def novo_id() -> str:
    return uuid.uuid4().hex


def agora() -> datetime:
    return datetime.now(UTC)


class Usuario(SQLModel, table=True):
    id: str = Field(default_factory=novo_id, primary_key=True)
    email: str = Field(unique=True, index=True)
    senha_hash: str | None = None  # preenchido a partir da etapa 5 (login)
    administrador: bool = False
    nascimento: date | None = None
    sexo: str | None = None  # "masculino" ou "feminino"
    ultimo_backup: datetime | None = None
    criado_em: datetime = Field(default_factory=agora)


class Registro(SQLModel):
    """Campos comuns a todo conteúdo de um usuário. Não é uma tabela."""

    id: str = Field(default_factory=novo_id, primary_key=True)
    usuario_id: str = Field(foreign_key="usuario.id", index=True)
    criado_em: datetime = Field(default_factory=agora)
    atualizado_em: datetime = Field(default_factory=agora)
    excluido_em: datetime | None = None


class Memoria(Registro, table=True):
    data: date = Field(index=True)
    texto: str
    emocao: str | None = None
    intensidade: int = 2
    marcante: bool = False
    silenciar: bool = False
    veio_de: list[str] = Field(default_factory=list, sa_column=Column(JSON, nullable=False))
    tags: list[str] = Field(default_factory=list, sa_column=Column(JSON, nullable=False))
    foto_arquivo: str | None = None  # nome do arquivo na pasta de fotos do dono


class Capitulo(Registro, table=True):
    nome: str
    inicio: date = Field(index=True)
    fim: date | None = None
    cor: str
    principal: bool = True
    categoria: str | None = None
    notas: str | None = None


class Intencao(Registro, table=True):
    nome: str
    horizonte: dict[str, Any] = Field(sa_column=Column(JSON, nullable=False))
    status: str = "ativa"
    notas: str | None = None
    memoria_id: str | None = Field(default=None, foreign_key="memoria.id")
