"""Ponto de entrada da API.

Por enquanto só existe a rota de saúde, usada para confirmar que o servidor
está no ar. As rotas de dados entram na etapa 2 do roteiro.
"""

from fastapi import FastAPI

from app import __version__

app = FastAPI(title="Vida em Semanas", version=__version__)


@app.get("/api/saude")
def saude() -> dict[str, str]:
    """Responde se o servidor está no ar e qual versão está rodando."""
    return {"status": "ok", "versao": __version__}
