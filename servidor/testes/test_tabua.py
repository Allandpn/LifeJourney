import math

import pytest

from app.nucleo.sobrevivencia import expectativa_sem_ajuste
from app.nucleo.tabua import Tabua, carregar_csv, carregar_tabua, estender_gompertz


@pytest.mark.parametrize("sexo, alvo", [("masculino", 20.8), ("feminino", 24.2)])
def test_tabua_provisoria_bate_a_expectativa_aos_60_do_ibge(modelo, sexo, alvo):
    assert expectativa_sem_ajuste(modelo.tabua(sexo), 60) == pytest.approx(alvo, abs=0.05)


@pytest.mark.parametrize("sexo", ["masculino", "feminino"])
def test_tabua_termina_na_idade_maxima(modelo, sexo):
    tabua = modelo.tabua(sexo)
    assert len(tabua.qx) == 121
    assert tabua.qx[-1] == 1.0
    assert all(0 < q <= 1 for q in tabua.qx)


def test_mortalidade_cresce_com_a_idade_na_vida_adulta(modelo):
    qx = modelo.tabua("masculino").qx
    assert all(qx[i] < qx[i + 1] for i in range(30, 120))


def test_mulheres_vivem_mais_que_homens_na_tabua(modelo):
    assert expectativa_sem_ajuste(modelo.tabua("feminino"), 0) > expectativa_sem_ajuste(
        modelo.tabua("masculino"), 0
    )


def test_extensao_de_gompertz_recupera_uma_curva_de_gompertz():
    # q_x exatos de mu(x) = 0,00005·e^(0,1x), com mu constante em cada ano (meio do ano)
    def q(x):
        return 1 - math.exp(-0.00005 * math.exp(0.1 * (x + 0.5)))

    conhecidos = {x: q(x) for x in range(0, 81)}  # inclui 80, que deve ser ignorado
    qx = estender_gompertz(conhecidos, ajuste_de=60, ajuste_ate=80, idade_maxima=110)

    assert qx[50] == conhecidos[50]
    assert qx[95] == pytest.approx(q(95), rel=1e-9)
    assert qx[-1] == 1.0


def test_extensao_reclama_de_idade_faltando():
    conhecidos = {x: 0.01 for x in range(0, 81) if x != 30}
    with pytest.raises(ValueError, match="idade 30"):
        estender_gompertz(conhecidos, 60, 80, 110)


def test_carrega_tabua_de_csv(tmp_path):
    linhas = ["idade,sexo,qx"]
    for x in range(0, 81):
        mu = 0.0001 * math.exp(0.09 * (x + 0.5))
        linhas.append(f"{x},masculino,{1 - math.exp(-mu):.8f}")
        linhas.append(f"{x},feminino,{1 - math.exp(-mu * 0.6):.8f}")
    arquivo = tmp_path / "tabua.csv"
    arquivo.write_text("\n".join(linhas), encoding="utf-8")

    homens = carregar_csv(arquivo, "masculino", 60, 80, 120)
    mulheres = carregar_tabua(
        {"tipo": "csv", "arquivo": "tabua.csv", "extensao_gompertz": {"de": 60, "ate": 80}},
        "feminino", 120, tmp_path,
    )

    assert isinstance(homens, Tabua) and len(homens.qx) == 121
    assert mulheres.qx[90] < homens.qx[90]


def test_sexo_invalido_e_recusado(modelo):
    with pytest.raises(ValueError):
        carregar_tabua(modelo.config["tabua"], "outro", 120, modelo.pasta_dados)
