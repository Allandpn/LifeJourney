"""Configuração do servidor, lida das variáveis de ambiente e do arquivo `.env`.

O `.env` fica na raiz do repositório e nunca vai para o git (ver `.env.exemplo`).
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

RAIZ_DO_REPOSITORIO = Path(__file__).resolve().parents[2]
BANCO_PADRAO = RAIZ_DO_REPOSITORIO / "dados-pessoais" / "lifejourney.db"
FOTOS_PADRAO = RAIZ_DO_REPOSITORIO / "dados-pessoais" / "fotos"

MODOS = ("desenvolvimento", "producao")


@dataclass(frozen=True)
class Configuracao:
    modo: str  # "desenvolvimento" ou "producao"
    caminho_banco: Path
    pasta_fotos: Path
    email_desenvolvimento: str  # conta criada por "python -m app.exemplo"
    cabecalho_do_ip: str | None = None  # ex.: "CF-Connecting-IP", atrás do túnel da Cloudflare
    pasta_do_aplicativo: Path | None = None  # aplicativo compilado (npm run build), servido em "/"
    origens_permitidas: tuple[str, ...] = ()  # endereços públicos do site, ex.: "pi.tailnet.ts.net"

    @property
    def desenvolvimento(self) -> bool:
        return self.modo == "desenvolvimento"


@lru_cache
def obter_configuracao() -> Configuracao:
    load_dotenv(RAIZ_DO_REPOSITORIO / ".env")
    modo = os.environ.get("LJ_MODO", "desenvolvimento")
    if modo not in MODOS:
        raise ValueError(f"LJ_MODO deve ser um de {MODOS}, e não '{modo}'.")
    banco = os.environ.get("LJ_BANCO")
    fotos = os.environ.get("LJ_FOTOS")
    return Configuracao(
        modo=modo,
        caminho_banco=Path(banco) if banco else BANCO_PADRAO,
        pasta_fotos=Path(fotos) if fotos else FOTOS_PADRAO,
        email_desenvolvimento=os.environ.get("LJ_EMAIL_DESENVOLVIMENTO", "dev@exemplo.local"),
        cabecalho_do_ip=os.environ.get("LJ_CABECALHO_DO_IP") or None,
        pasta_do_aplicativo=Path(os.environ["LJ_APLICATIVO"]) if os.environ.get("LJ_APLICATIVO") else None,
        origens_permitidas=tuple(o.strip().lower() for o in os.environ.get("LJ_ORIGENS_PERMITIDAS", "").split(",") if o.strip()),
    )
