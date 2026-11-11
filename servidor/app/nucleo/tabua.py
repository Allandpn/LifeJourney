"""Tábua de mortalidade: probabilidade anual de morte `q_x` por idade e sexo.

Há duas origens possíveis, escolhidas em `dados/fatores.json`:

- `gompertz_makeham_provisoria`: curva matemática usada até a tábua do IBGE
  estar no projeto (é a mesma base do protótipo descrito no briefing);
- `csv`: arquivo `idade,sexo,qx` (formato da tábua do IBGE), estendido acima
  de 80 anos por uma curva de Gompertz ajustada às idades de 60 a 80.
"""

from __future__ import annotations

import csv
import math
from dataclasses import dataclass
from pathlib import Path

SEXOS = ("masculino", "feminino")


@dataclass(frozen=True)
class Tabua:
    """`qx[i]` é a probabilidade de morrer entre as idades i e i+1."""

    sexo: str
    qx: tuple[float, ...]

    def risco_instantaneo(self, idade: float) -> float:
        """Taxa instantânea de morte (por ano) na idade dada.

        Dentro de cada ano de idade a taxa é constante: mu = -ln(1 - q_x).
        """
        i = int(idade)
        if i >= len(self.qx):
            return math.inf
        q = self.qx[i]
        return math.inf if q >= 1 else -math.log(1 - q)


def _qx_gompertz_makeham(a: float, b: float, c: float, idade_maxima: int) -> tuple[float, ...]:
    """q_x anual da curva mu(x) = a·e^(b·x) + c, integrada em cada ano de idade."""
    qx = []
    for x in range(idade_maxima):
        risco_acumulado = a / b * (math.exp(b * (x + 1)) - math.exp(b * x)) + c
        qx.append(1 - math.exp(-risco_acumulado))
    qx.append(1.0)  # na idade máxima a curva termina
    return tuple(qx)


def gompertz_makeham_provisoria(
    sexo: str, b: float, c: float, expectativa_aos_60: float, idade_maxima: int
) -> Tabua:
    """Tábua provisória: ajusta `a` para que a expectativa aos 60 bata com o alvo.

    O alvo vem da tábua do IBGE 2024 (homens 20,8; mulheres 24,2 anos).
    """
    # importação aqui para evitar dependência circular entre os módulos
    from app.nucleo.sobrevivencia import expectativa_sem_ajuste

    def expectativa(a: float) -> float:
        return expectativa_sem_ajuste(Tabua(sexo, _qx_gompertz_makeham(a, b, c, idade_maxima)), 60)

    # quanto maior `a`, menor a expectativa: busca binária na escala logarítmica
    baixo, alto = 1e-8, 1e-2
    for _ in range(80):
        meio = math.sqrt(baixo * alto)
        if expectativa(meio) > expectativa_aos_60:
            baixo = meio
        else:
            alto = meio
    return Tabua(sexo, _qx_gompertz_makeham(math.sqrt(baixo * alto), b, c, idade_maxima))


def estender_gompertz(
    qx_conhecidos: dict[int, float], ajuste_de: int, ajuste_ate: int, idade_maxima: int
) -> tuple[float, ...]:
    """Completa a tábua acima da última idade conhecida com uma curva de Gompertz.

    Ajusta uma reta a ln(mu_x) nas idades de `ajuste_de` até `ajuste_ate - 1`
    (mínimos quadrados) e usa a reta para as idades seguintes. O mu tirado de
    q_x vale para o ano inteiro de x a x+1, por isso ele é posto no meio do ano.
    """
    idades = [x for x in range(ajuste_de, ajuste_ate) if x in qx_conhecidos]
    if len(idades) < 2:
        raise ValueError("São precisas ao menos duas idades para ajustar a curva de Gompertz.")
    meios = [x + 0.5 for x in idades]
    logs = [math.log(-math.log(1 - qx_conhecidos[x])) for x in idades]
    media_x = sum(meios) / len(meios)
    media_y = sum(logs) / len(logs)
    inclinacao = sum((x - media_x) * (y - media_y) for x, y in zip(meios, logs)) / sum(
        (x - media_x) ** 2 for x in meios
    )
    intercepto = media_y - inclinacao * media_x

    ultima = max(qx_conhecidos)
    qx = []
    for x in range(idade_maxima):
        if x in qx_conhecidos and x < ajuste_ate:
            qx.append(qx_conhecidos[x])
        elif x <= ultima and x < ajuste_ate:
            raise ValueError(f"Falta a idade {x} na tábua.")
        else:
            mu = math.exp(intercepto + inclinacao * (x + 0.5))
            qx.append(1 - math.exp(-mu))
    qx.append(1.0)
    return tuple(qx)


def estender_pela_expectativa(
    qx_conhecidos: dict[int, float], expectativa_aberta: float, idade_maxima: int
) -> tuple[float, ...]:
    """Completa a tábua acima da última idade com uma curva de Gompertz calibrada.

    A curva parte do risco da última idade publicada e sobe com a inclinação que faz a
    expectativa de vida no grupo aberto (ex.: "90 ou mais") bater com a que o IBGE publica.
    Usa a própria informação da tábua, em vez de só extrapolar a tendência dos 60 aos 89.
    """
    from app.nucleo.sobrevivencia import expectativa_sem_ajuste

    ultima = max(qx_conhecidos)
    if sorted(qx_conhecidos) != list(range(ultima + 1)):
        raise ValueError("A tábua precisa ter todas as idades de 0 até a última.")
    mu_ultima = -math.log(1 - qx_conhecidos[ultima])
    conhecidos = [qx_conhecidos[x] for x in range(ultima + 1)]

    def montar(inclinacao: float) -> tuple[float, ...]:
        extra = [1 - math.exp(-mu_ultima * math.exp(inclinacao * (x - ultima))) for x in range(ultima + 1, idade_maxima)]
        return tuple(conhecidos + extra + [1.0])

    # inclinação maior = mortes mais rápidas = expectativa menor
    baixo, alto = 0.0, 1.0
    for _ in range(60):
        meio = (baixo + alto) / 2
        if expectativa_sem_ajuste(Tabua("calibracao", montar(meio)), ultima + 1) > expectativa_aberta:
            baixo = meio
        else:
            alto = meio
    return montar((baixo + alto) / 2)


def carregar_csv(
    caminho: Path | str, sexo: str, ajuste_de: int, ajuste_ate: int, idade_maxima: int,
    expectativa_aberta: float | None = None,
) -> Tabua:
    """Lê um CSV `idade,sexo,qx` e estende acima de `ajuste_ate` com Gompertz.

    As idades a partir de `ajuste_ate` (o grupo aberto 80+ da tábua do IBGE) são
    ignoradas e substituídas pela extensão.
    """
    conhecidos: dict[int, float] = {}
    with open(caminho, encoding="utf-8") as arquivo:
        for linha in csv.DictReader(arquivo):
            if linha["sexo"].strip() == sexo:
                conhecidos[int(linha["idade"])] = float(linha["qx"])
    if not conhecidos:
        raise ValueError(f"Nenhuma linha para o sexo '{sexo}' em {caminho}.")
    if expectativa_aberta is not None:
        return Tabua(sexo, estender_pela_expectativa(conhecidos, expectativa_aberta, idade_maxima))
    return Tabua(sexo, estender_gompertz(conhecidos, ajuste_de, ajuste_ate, idade_maxima))


def carregar_tabua(config_tabua: dict, sexo: str, idade_maxima: int, pasta: Path) -> Tabua:
    """Cria a tábua indicada na configuração."""
    if sexo not in SEXOS:
        raise ValueError(f"Sexo deve ser um de {SEXOS}.")
    tipo = config_tabua["tipo"]
    if tipo == "gompertz_makeham_provisoria":
        return gompertz_makeham_provisoria(
            sexo,
            b=config_tabua["b"],
            c=config_tabua["c"],
            expectativa_aos_60=config_tabua["expectativa_aos_60"][sexo],
            idade_maxima=idade_maxima,
        )
    if tipo == "csv":
        extensao = config_tabua["extensao_gompertz"]
        aberta = config_tabua.get("expectativa_no_grupo_aberto", {}).get(sexo)
        return carregar_csv(
            pasta / config_tabua["arquivo"], sexo, extensao["de"], extensao["ate"], idade_maxima, aberta
        )
    raise ValueError(f"Tipo de tábua desconhecido: {tipo}")
