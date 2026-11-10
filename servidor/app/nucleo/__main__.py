"""Mostra o cálculo para um perfil de exemplo fictício.

Rode, dentro da pasta `servidor`:  python -m app.nucleo
"""

from datetime import date

from app.nucleo import Perfil, carregar_modelo


def anos(x: float) -> str:
    return f"{x:5.1f}".replace(".", ",")


def main() -> None:
    modelo = carregar_modelo()
    perfil = Perfil(nascimento=date(1990, 3, 14), sexo="feminino", data_calculo=date.today())
    respostas = {
        "tabagismo": "nunca",
        "imc": modelo.categoria_imc(1.65, 70),
        "alcool": "ate_7",
        "atividade": "30_a_150",
        "sono": "menos_de_6",
        "vinculos": "1_a_2",
    }
    sem = modelo.parametros.semanas_por_ano

    print(f"Configuração: {modelo.versao}")
    print(f"Perfil de exemplo: {perfil.sexo}, {anos(perfil.idade)} anos\n")
    print("                      HR    média   P10  mediana   P90")
    for nome, r in [("brasileira média", modelo.calcular(perfil)),
                    ("perfil de exemplo", modelo.calcular(perfil, respostas))]:
        print(f"{nome:<18} {r.hr_total:5.2f}  {anos(r.expectativa_media)} {anos(r.p10)}  "
              f"{anos(r.mediana)}  {anos(r.p90)}")

    print("\nE se?")
    for m in modelo.e_se(perfil, respostas):
        nome = "todas juntas" if m.fator == "todas" else f"{m.fator}: {m.alternativa}"
        print(f"  {nome:<28} HR {m.hr_total:4.2f}   {m.ganho_semanas:+5.0f} semanas")
    print(f"\n(1 ano = {sem} semanas)")


if __name__ == "__main__":
    main()
