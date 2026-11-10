"""Ponto de entrada da API.

Rode, dentro da pasta `servidor`:  uvicorn app.principal:app --reload
A documentação automática fica em http://127.0.0.1:8000/docs
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app import __version__
from app.api import capitulos, estimativa, intencoes, memorias, perfil
from app.banco import criar_tabelas, obter_motor
from app.config import obter_configuracao

log = logging.getLogger(__name__)


@asynccontextmanager
async def ciclo_de_vida(_app: FastAPI):
    config = obter_configuracao()
    criar_tabelas(obter_motor())
    if config.desenvolvimento:
        log.warning("Modo desenvolvimento: sem login, todas as requisições são de %s.", config.email_desenvolvimento)
    yield


app = FastAPI(
    title="Vida em Semanas",
    version=__version__,
    description="API do Vida em Semanas. Até a etapa 5 não há login: em modo desenvolvimento, "
    "tudo é gravado para um usuário de desenvolvimento.",
    lifespan=ciclo_de_vida,
)

for modulo in (perfil, memorias, capitulos, intencoes, estimativa):
    app.include_router(modulo.rotas)


@app.get("/api/saude", tags=["servidor"])
def saude() -> dict[str, str]:
    """Responde se o servidor está no ar e qual versão está rodando."""
    return {"status": "ok", "versao": __version__}
