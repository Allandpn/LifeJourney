"""Ponto de entrada da API.

Rode, dentro da pasta `servidor`:  uvicorn app.principal:app --reload
A documentação automática fica em http://127.0.0.1:8000/docs (só em desenvolvimento).
"""

from contextlib import asynccontextmanager
from urllib.parse import urlsplit

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app import __version__
from app.api import admin, capitulos, contas, estimativa, intencoes, memorias, perfil
from app.banco import criar_tabelas, obter_motor
from app.config import obter_configuracao

METODOS_SEGUROS = {"GET", "HEAD", "OPTIONS"}


def conferir_conta_de_desenvolvimento(motor) -> None:
    """Em produção, recusa ligar se a conta de desenvolvimento ainda tiver a senha conhecida.

    Isso acontece se o banco de desenvolvimento for levado para o servidor de verdade.
    """
    from sqlmodel import Session, select

    from app.exemplo import SENHA_DE_DESENVOLVIMENTO
    from app.modelos import Usuario
    from app.seguranca import senha_confere

    config = obter_configuracao()
    if config.desenvolvimento:
        return
    with Session(motor) as sessao:
        dev = sessao.exec(select(Usuario).where(Usuario.email == config.email_desenvolvimento)).first()
        if dev and senha_confere(dev.senha_hash, SENHA_DE_DESENVOLVIMENTO):
            raise RuntimeError(
                f"A conta {dev.email} usa a senha de desenvolvimento. Troque-a com "
                f"'python -m app.contas redefinir-senha {dev.email}' antes de ligar em produção."
            )


@asynccontextmanager
async def ciclo_de_vida(_app: FastAPI):
    motor = obter_motor()
    criar_tabelas(motor)
    conferir_conta_de_desenvolvimento(motor)
    yield


_desenvolvimento = obter_configuracao().desenvolvimento
app = FastAPI(
    title="Vida em Semanas",
    version=__version__,
    lifespan=ciclo_de_vida,
    # em produção, sem documentação pública da API
    docs_url="/docs" if _desenvolvimento else None,
    redoc_url=None,
    openapi_url="/openapi.json" if _desenvolvimento else None,
)

for modulo in (contas, admin, perfil, memorias, capitulos, intencoes, estimativa):
    app.include_router(modulo.rotas)


@app.middleware("http")
async def protecoes(request: Request, chamar):
    """Recusa pedidos que alteram dados vindos de outro site, e acrescenta cabeçalhos de segurança.

    O cookie já é SameSite=Lax; conferir a origem é uma segunda barreira.
    """
    if request.method not in METODOS_SEGUROS:
        origem = request.headers.get("origin")
        if origem:
            host = request.headers.get("x-forwarded-host") or request.headers.get("host")
            if urlsplit(origem).netloc != host:
                return JSONResponse({"detail": "Pedido de outro site recusado."}, status_code=403)
    resposta = await chamar(request)
    resposta.headers.setdefault("X-Content-Type-Options", "nosniff")
    resposta.headers.setdefault("X-Frame-Options", "DENY")
    resposta.headers.setdefault("Referrer-Policy", "no-referrer")
    if request.url.path.startswith("/api/") and "cache-control" not in resposta.headers:
        resposta.headers["Cache-Control"] = "no-store"  # respostas com dados pessoais não ficam em cache
    return resposta


@app.get("/api/saude", tags=["servidor"])
def saude() -> dict[str, str]:
    """Responde se o servidor está no ar e qual versão está rodando."""
    return {"status": "ok", "versao": __version__}
