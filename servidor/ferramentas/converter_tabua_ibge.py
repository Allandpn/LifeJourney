"""Converte as planilhas da Tábua Completa de Mortalidade do IBGE no CSV que o núcleo lê.

O IBGE publica uma tábua nova todo ano, até 1º de dezembro, em:
    https://ftp.ibge.gov.br/Tabuas_Completas_de_Mortalidade/Tabuas_Completas_de_Mortalidade_<ANO>/xlsx/
Baixe homens.xlsx e mulheres.xlsx e rode, dentro da pasta `servidor`:

    python ferramentas/converter_tabua_ibge.py homens.xlsx mulheres.xlsx dados/tabua-ibge-<ANO>.csv

Saída: `idade,sexo,qx`, com q_x como probabilidade (0 a 1), só para as idades simples.
O grupo aberto do fim da tábua ("90 ou mais") fica de fora: acima dele o núcleo usa
uma curva de Gompertz. Depois, troque o arquivo em dados/fatores.json e rode os testes.
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

import openpyxl


def ler_planilha(caminho: Path) -> tuple[str, list[tuple[int, float]], dict[int, float]]:
    """Devolve o título, os pares (idade, q_x) e a expectativa e(x) publicada em cada idade."""
    planilha = openpyxl.load_workbook(caminho, read_only=True, data_only=True).worksheets[0]
    linhas = list(planilha.iter_rows(values_only=True))
    titulo = next(str(l[0]).strip() for l in linhas if l and isinstance(l[0], str) and "Tábua" in l[0])
    qx: list[tuple[int, float]] = []
    expectativa: dict[int, float] = {}
    for linha in linhas:
        idade, q_por_mil, *_resto = linha[:7]
        e_x = linha[6]
        if isinstance(idade, (int, float)) and isinstance(q_por_mil, (int, float)):
            idade = int(idade)
            expectativa[idade] = float(e_x)
            if q_por_mil < 1000:  # 1000 por mil = grupo aberto, que fica de fora
                qx.append((idade, q_por_mil / 1000))
        elif isinstance(idade, str) and "ou mais" in idade:
            expectativa[int(idade.split()[0])] = float(e_x)  # e(x) do grupo aberto, útil para conferir
    idades = [i for i, _ in qx]
    if idades != list(range(len(idades))):
        raise ValueError(f"{caminho}: as idades simples não estão completas a partir de 0.")
    return titulo, qx, expectativa


def main(argumentos: list[str]) -> int:
    if len(argumentos) != 3:
        print(__doc__)
        return 1
    homens, mulheres, saida = (Path(a) for a in argumentos)
    with open(saida, "w", newline="", encoding="utf-8") as arquivo:
        escritor = csv.writer(arquivo, lineterminator="\n")
        escritor.writerow(["idade", "sexo", "qx"])
        for sexo, planilha in (("masculino", homens), ("feminino", mulheres)):
            titulo, qx, expectativa = ler_planilha(planilha)
            if ("Homens" in titulo) != (sexo == "masculino"):
                raise ValueError(f"{planilha} parece ser de outro sexo: {titulo}")
            for idade, q in qx:
                escritor.writerow([idade, sexo, f"{q:.10f}"])
            ultima = qx[-1][0]
            print(f"{sexo}: idades 0 a {ultima}; e(0) = {expectativa[0]:.2f}; e(60) = {expectativa[60]:.2f}; "
                  f"e({ultima + 1}+) = {expectativa.get(ultima + 1, float('nan')):.2f}  ({titulo})")
    print(f"Gravado em {saida}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
