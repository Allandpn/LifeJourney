"""Fatores do questionário: de respostas a um risco combinado (HR_total).

Regras (docs/05-modelo-de-calculo.md):

1. cada HR é dividido pela média brasileira daquele fator (recentragem);
2. fatores do bloco "marcador" entram juntos, com peso reduzido;
3. o total fica entre o piso e o teto;
4. pergunta pulada conta como a média brasileira (contribui 1,0).
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Callable

from app.nucleo.configuracao import Parametros

# Converte "anos de vida perdidos numa idade" em HR, usando a tábua ativa.
ConversorDePerda = Callable[[float, float], float]


@dataclass(frozen=True)
class Fator:
    chave: str
    pergunta: str
    bloco: str  # "causal" ou "marcador"
    hrs: dict[str, float]  # resposta -> HR relativo à categoria de referência do estudo
    media_br: float  # HR médio da população brasileira
    e_se: dict[str, str]  # resposta atual -> alternativa mais saudável


def _hr_da_resposta(definicao: dict, converter_perda: ConversorDePerda) -> float:
    if "hr" in definicao:
        return float(definicao["hr"])
    if "perda_anos" in definicao:
        return converter_perda(definicao["perda_anos"], definicao["idade_referencia"])
    raise ValueError(f"Resposta sem 'hr' nem 'perda_anos': {definicao}")


def _media_br(definicao: dict, hrs: dict[str, float], chave: str) -> float:
    """Média do HR na população: valor direto ou média ponderada pelas prevalências."""
    if "prevalencias" in definicao:
        prevalencias = definicao["prevalencias"]
        total = sum(prevalencias.values())
        if not math.isclose(total, 1.0, abs_tol=0.01):
            raise ValueError(f"Prevalências de '{chave}' somam {total:.3f}, e não 1.")
        return sum(hrs[r] * peso for r, peso in prevalencias.items()) / total
    return float(definicao["valor"])


def ler_fatores(config: dict, converter_perda: ConversorDePerda) -> dict[str, Fator]:
    fatores = {}
    for chave, f in config["fatores"].items():
        hrs = {r: _hr_da_resposta(d, converter_perda) for r, d in f["respostas"].items()}
        for atual, alternativa in f.get("e_se", {}).items():
            if atual not in hrs or alternativa not in hrs:
                raise ValueError(f"'e_se' de '{chave}' cita resposta inexistente.")
        fatores[chave] = Fator(
            chave=chave,
            pergunta=f["pergunta"],
            bloco=f["bloco"],
            hrs=hrs,
            media_br=_media_br(f["media_br"], hrs, chave),
            e_se=dict(f.get("e_se", {})),
        )
    return fatores


def hr_combinado(fatores: dict[str, Fator], respostas: dict[str, str], p: Parametros) -> float:
    """HR_total = clamp(produto dos causais × exp(redutor × soma dos log dos marcadores))."""
    desconhecidos = set(respostas) - set(fatores)
    if desconhecidos:
        raise ValueError(f"Fatores desconhecidos: {sorted(desconhecidos)}")

    produto_causais = 1.0
    soma_log_marcadores = 0.0
    for chave, resposta in respostas.items():
        fator = fatores[chave]
        if resposta not in fator.hrs:
            raise ValueError(f"Resposta '{resposta}' não existe para '{chave}'.")
        relativo = fator.hrs[resposta] / fator.media_br
        if fator.bloco == "marcador":
            soma_log_marcadores += math.log(relativo)
        else:
            produto_causais *= relativo

    total = produto_causais * math.exp(p.redutor_marcadores * soma_log_marcadores)
    return min(p.hr_maximo, max(p.hr_minimo, total))


def categoria_imc(altura_m: float, peso_kg: float, faixas: list[dict]) -> str:
    """Devolve a resposta de IMC (ex.: "25_a_27_5") para altura e peso."""
    if altura_m <= 0 or peso_kg <= 0:
        raise ValueError("Altura e peso precisam ser positivos.")
    imc = peso_kg / altura_m**2
    for faixa in faixas:
        if imc < faixa["abaixo_de"]:
            return faixa["resposta"]
    return faixas[-1]["resposta_acima"]
