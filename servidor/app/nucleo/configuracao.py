"""Leitura do arquivo de configuração do modelo (`dados/fatores.json`)."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

PASTA_DADOS = Path(__file__).resolve().parents[2] / "dados"
ARQUIVO_PADRAO = PASTA_DADOS / "fatores.json"


@dataclass(frozen=True)
class Parametros:
    """Números provisórios do modelo, todos vindos da configuração."""

    atenuacao_inicio: float  # idade em que o efeito dos fatores começa a encolher
    atenuacao_fim: float  # idade em que o efeito dos fatores chega a zero
    redutor_marcadores: float  # peso do bloco de marcadores (0,5 = metade)
    hr_minimo: float  # piso do risco combinado
    hr_maximo: float  # teto do risco combinado
    idade_maxima: float  # idade em que a curva termina
    passos_por_ano: int  # 12 = passos mensais
    semanas_por_ano: float


def ler_json(caminho: Path | str = ARQUIVO_PADRAO) -> dict:
    """Lê o arquivo de configuração e devolve o dicionário."""
    with open(caminho, encoding="utf-8") as arquivo:
        return json.load(arquivo)


def ler_parametros(config: dict) -> Parametros:
    p = config["parametros"]
    return Parametros(
        atenuacao_inicio=p["atenuacao"]["inicio"],
        atenuacao_fim=p["atenuacao"]["fim"],
        redutor_marcadores=p["redutor_marcadores"]["valor"],
        hr_minimo=p["limites_hr"]["minimo"],
        hr_maximo=p["limites_hr"]["maximo"],
        idade_maxima=p["idade_maxima"],
        passos_por_ano=p["passos_por_ano"],
        semanas_por_ano=p["semanas_por_ano"],
    )
