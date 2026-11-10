"""Curva de sobrevivência ajustada e as saídas do modelo (percentis e média).

Método de tábua de vida, em passos de 1/`passos_por_ano` de ano:

    risco ajustado = mu(x) · HR(x)                 (equivale a q'_x = 1 - (1 - q_x)^HR)
    HR(x) = 1 + (HR_total - 1) · w(x)               (atenuação com a idade)
    S(x) = produto de e^(-risco ajustado · passo)   (sobrevivência a partir da idade atual)
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from app.nucleo.configuracao import Parametros
from app.nucleo.tabua import Tabua


def peso_da_idade(idade: float, inicio: float, fim: float) -> float:
    """w(x): 1 antes de `inicio`, cai em linha reta até 0 em `fim`."""
    if idade < inicio:
        return 1.0
    if idade >= fim:
        return 0.0
    return (fim - idade) / (fim - inicio)


def hr_na_idade(hr_total: float, idade: float, inicio: float, fim: float) -> float:
    """HR(x) = 1 + (HR_total - 1) · w(x)."""
    return 1 + (hr_total - 1) * peso_da_idade(idade, inicio, fim)


@dataclass(frozen=True)
class Resultado:
    """Saídas do modelo. Idades em anos; a curva serve para desenhar o futuro."""

    idade_atual: float
    hr_total: float
    expectativa_media: float  # idade média de morte
    p10: float  # idade em que a sobrevivência cai abaixo de 0,9
    mediana: float  # idade em que a sobrevivência cai abaixo de 0,5
    p90: float  # idade em que a sobrevivência cai abaixo de 0,1
    curva: tuple[tuple[float, float], ...]  # pares (idade, S)

    def em_semanas(self, idade: float, semanas_por_ano: float) -> float:
        """Converte uma idade em semanas de vida."""
        return idade * semanas_por_ano


def curva_de_sobrevivencia(
    tabua: Tabua, idade_atual: float, hr_total: float, p: Parametros
) -> tuple[tuple[float, float], ...]:
    """Pontos (idade, S) da idade atual até a idade máxima."""
    passo = 1 / p.passos_por_ano
    idade, s = idade_atual, 1.0
    pontos = [(idade, s)]
    while idade < p.idade_maxima - 1e-9 and s > 0:
        meio = idade + passo / 2
        risco = tabua.risco_instantaneo(meio)
        if math.isinf(risco):
            s = 0.0
        else:
            hr = hr_na_idade(hr_total, meio, p.atenuacao_inicio, p.atenuacao_fim)
            s *= math.exp(-risco * hr * passo)
        idade += passo
        pontos.append((idade, s))
    return tuple(pontos)


def idade_em_que_cai_abaixo(curva: tuple[tuple[float, float], ...], limiar: float) -> float:
    """Primeira idade em que S fica abaixo do limiar, interpolando dentro do passo."""
    for (x0, s0), (x1, s1) in zip(curva, curva[1:]):
        if s1 < limiar <= s0:
            return x0 + (s0 - limiar) / (s0 - s1) * (x1 - x0)
    return curva[-1][0]


def expectativa_media(curva: tuple[tuple[float, float], ...]) -> float:
    """Idade atual + área sob a curva de sobrevivência (regra do trapézio)."""
    area = sum((x1 - x0) * (s0 + s1) / 2 for (x0, s0), (x1, s1) in zip(curva, curva[1:]))
    return curva[0][0] + area


def calcular_resultado(tabua: Tabua, idade_atual: float, hr_total: float, p: Parametros) -> Resultado:
    curva = curva_de_sobrevivencia(tabua, idade_atual, hr_total, p)
    return Resultado(
        idade_atual=idade_atual,
        hr_total=hr_total,
        expectativa_media=expectativa_media(curva),
        p10=idade_em_que_cai_abaixo(curva, 0.9),
        mediana=idade_em_que_cai_abaixo(curva, 0.5),
        p90=idade_em_que_cai_abaixo(curva, 0.1),
        curva=curva,
    )


# Parâmetros neutros usados para validar a tábua (sem fatores, sem atenuação).
_SEM_AJUSTE = Parametros(
    atenuacao_inicio=200, atenuacao_fim=201, redutor_marcadores=0, hr_minimo=1, hr_maximo=1,
    idade_maxima=120, passos_por_ano=12, semanas_por_ano=52.1775,
)


def expectativa_sem_ajuste(tabua: Tabua, idade: float) -> float:
    """Anos de vida restantes na idade dada, só com a tábua (HR = 1)."""
    p = Parametros(**{**_SEM_AJUSTE.__dict__, "idade_maxima": len(tabua.qx)})
    return expectativa_media(curva_de_sobrevivencia(tabua, idade, 1.0, p)) - idade
