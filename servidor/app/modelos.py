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


def em_utc(momento: datetime) -> datetime:
    """O SQLite devolve datas sem fuso; todas foram gravadas em UTC."""
    return momento if momento.tzinfo else momento.replace(tzinfo=UTC)


class Usuario(SQLModel, table=True):
    id: str = Field(default_factory=novo_id, primary_key=True)
    email: str = Field(unique=True, index=True)
    senha_hash: str | None = None  # hash Argon2; sem senha, a conta não consegue entrar
    administrador: bool = False
    nascimento: date | None = None
    sexo: str | None = None  # "masculino" ou "feminino"
    ultimo_backup: datetime | None = None
    criado_em: datetime = Field(default_factory=agora)


class Sessao(SQLModel, table=True):
    """Um aparelho conectado. O cookie do aparelho tem o código; aqui fica só o hash."""

    id: str = Field(default_factory=novo_id, primary_key=True)  # usado para listar e desconectar
    codigo_hash: str = Field(unique=True, index=True)
    usuario_id: str = Field(foreign_key="usuario.id", index=True)
    aparelho: str = ""
    criado_em: datetime = Field(default_factory=agora)
    ultimo_uso: datetime = Field(default_factory=agora)
    expira_em: datetime


class Convite(SQLModel, table=True):
    """Link para criar uma conta. Vale uma vez, por poucos dias."""

    id: str = Field(default_factory=novo_id, primary_key=True)
    codigo_hash: str = Field(unique=True, index=True)
    criado_por: str = Field(foreign_key="usuario.id")
    criado_em: datetime = Field(default_factory=agora)
    valido_ate: datetime
    usado_por: str | None = Field(default=None, foreign_key="usuario.id")
    cancelado_em: datetime | None = None


class Redefinicao(SQLModel, table=True):
    """Link para criar senha nova, gerado pelo administrador. Vale uma vez, por um dia."""

    id: str = Field(default_factory=novo_id, primary_key=True)
    codigo_hash: str = Field(unique=True, index=True)
    usuario_id: str = Field(foreign_key="usuario.id")
    criado_em: datetime = Field(default_factory=agora)
    valido_ate: datetime
    usado_em: datetime | None = None


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


class RespostasDeSaude(Registro, table=True):
    """Uma rodada do questionário. Cada envio cria uma nova, para formar o histórico.

    São dados de saúde: ao apagar, o registro sai de verdade do banco (não só marcado).
    """

    __tablename__ = "respostas_de_saude"

    respostas: dict[str, str] = Field(sa_column=Column(JSON, nullable=False))  # fator -> resposta (com o IMC já em faixa)
    altura_m: float | None = None
    peso_kg: float | None = None
    versao_config: str
    resultado: dict[str, Any] = Field(sa_column=Column(JSON, nullable=False))  # risco e faixa no dia do envio
