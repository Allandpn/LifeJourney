"""Formato dos dados que entram e saem da API, com as regras de validação.

Para cada entidade há três formatos:
- `...Dados`: o que o aplicativo envia para criar (todos os campos);
- `...Mudancas`: o que envia para alterar (só os campos que mudaram);
- `...Lida`: o que a API devolve (os dados mais id e datas).
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator, model_validator

LIMITE_TEXTO_MEMORIA = 280  # em avaliação (docs/08-decisoes.md)

Emocao = Literal["alegria", "calma", "orgulho", "saudade", "tristeza", "incerteza"]
CorCapitulo = Literal["menta", "azul", "ambar", "laranja", "rosa", "lavanda", "coral"]
StatusIntencao = Literal["ativa", "pausada", "virou_memoria", "deixada_de_lado"]
Sexo = Literal["masculino", "feminino"]

TextoCurto = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=120)]
TextoMemoria = Annotated[
    str, StringConstraints(strip_whitespace=True, min_length=1, max_length=LIMITE_TEXTO_MEMORIA)
]
Notas = Annotated[str, StringConstraints(strip_whitespace=True, max_length=5000)]
Tag = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=40)]


class Esquema(BaseModel):
    model_config = ConfigDict(extra="forbid")  # recusa campos desconhecidos


class Lido(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    criado_em: datetime
    atualizado_em: datetime


# ---------- Perfil ----------

class PerfilDados(Esquema):
    nascimento: date
    sexo: Sexo

    @field_validator("nascimento")
    @classmethod
    def _nascimento_valido(cls, valor: date) -> date:
        if valor > date.today():
            raise ValueError("A data de nascimento não pode estar no futuro.")
        if valor.year < 1900:
            raise ValueError("A data de nascimento precisa ser de 1900 em diante.")
        return valor


class PerfilLido(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    email: str
    nascimento: date | None
    sexo: Sexo | None
    ultimo_backup: datetime | None


# ---------- Memória ----------

class MemoriaDados(Esquema):
    data: date
    texto: TextoMemoria
    emocao: Emocao | None = None
    intensidade: int = Field(default=2, ge=1, le=3)
    marcante: bool = False
    silenciar: bool = False
    veio_de: list[str] = Field(default_factory=list, max_length=20)
    tags: list[Tag] = Field(default_factory=list, max_length=20)

    @field_validator("data")
    @classmethod
    def _data_no_passado(cls, valor: date) -> date:
        if valor > date.today():
            raise ValueError("Uma memória não pode ter data no futuro. Para planos, use uma intenção.")
        return valor

    @field_validator("veio_de", "tags")
    @classmethod
    def _sem_repeticao(cls, valores: list[str]) -> list[str]:
        return list(dict.fromkeys(valores))


class MemoriaMudancas(Esquema):
    data: date | None = None
    texto: TextoMemoria | None = None
    emocao: Emocao | None = None
    intensidade: int | None = Field(default=None, ge=1, le=3)
    marcante: bool | None = None
    silenciar: bool | None = None
    veio_de: list[str] | None = None
    tags: list[Tag] | None = None


class MemoriaLida(Lido, MemoriaDados):
    model_config = ConfigDict(from_attributes=True, extra="ignore")

    levou_a: list[str] = Field(default_factory=list, description="Memórias que apontam para esta em 'veio_de'.")


# ---------- Capítulo ----------

class CapituloDados(Esquema):
    nome: TextoCurto
    inicio: date
    fim: date | None = None
    cor: CorCapitulo
    principal: bool = True
    categoria: TextoCurto | None = None
    notas: Notas | None = None

    @model_validator(mode="after")
    def _fim_depois_do_inicio(self) -> CapituloDados:
        if self.fim is not None and self.fim < self.inicio:
            raise ValueError("O fim do capítulo não pode ser antes do início.")
        return self


class CapituloMudancas(Esquema):
    nome: TextoCurto | None = None
    inicio: date | None = None
    fim: date | None = None
    cor: CorCapitulo | None = None
    principal: bool | None = None
    categoria: TextoCurto | None = None
    notas: Notas | None = None


class CapituloLido(Lido, CapituloDados):
    model_config = ConfigDict(from_attributes=True, extra="ignore")


# ---------- Intenção ----------

class HorizonteData(Esquema):
    tipo: Literal["data"]
    data: date


class HorizonteIntervalo(Esquema):
    tipo: Literal["intervalo"]
    de: date
    ate: date

    @model_validator(mode="after")
    def _ordem(self) -> HorizonteIntervalo:
        if self.ate < self.de:
            raise ValueError("O fim do intervalo não pode ser antes do começo.")
        return self


class HorizonteAlgumDia(Esquema):
    tipo: Literal["algum_dia"]


Horizonte = Annotated[HorizonteData | HorizonteIntervalo | HorizonteAlgumDia, Field(discriminator="tipo")]


class IntencaoDados(Esquema):
    nome: TextoCurto
    horizonte: Horizonte
    status: StatusIntencao = "ativa"
    notas: Notas | None = None
    memoria_id: str | None = None


class IntencaoMudancas(Esquema):
    nome: TextoCurto | None = None
    horizonte: Horizonte | None = None
    status: StatusIntencao | None = None
    notas: Notas | None = None
    memoria_id: str | None = None


class IntencaoLida(Lido, IntencaoDados):
    model_config = ConfigDict(from_attributes=True, extra="ignore")
