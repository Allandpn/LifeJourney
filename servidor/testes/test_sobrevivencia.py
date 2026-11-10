import pytest

from app.nucleo.sobrevivencia import (
    calcular_resultado,
    curva_de_sobrevivencia,
    hr_na_idade,
    peso_da_idade,
)
from conftest import perfil


def test_peso_da_idade_cai_de_75_a_95():
    assert peso_da_idade(50, 75, 95) == 1
    assert peso_da_idade(85, 75, 95) == pytest.approx(0.5)
    assert peso_da_idade(95, 75, 95) == 0
    assert peso_da_idade(110, 75, 95) == 0


def test_hr_atenuado_volta_a_1_em_idade_avancada():
    assert hr_na_idade(2.0, 60, 75, 95) == 2.0
    assert hr_na_idade(2.0, 85, 75, 95) == pytest.approx(1.5)
    assert hr_na_idade(2.0, 100, 75, 95) == 1.0


@pytest.mark.parametrize("hr", [0.4, 1.0, 4.0])
def test_curva_comeca_em_1_e_nunca_sobe(modelo, hr):
    curva = curva_de_sobrevivencia(modelo.tabua("masculino"), 38.4, hr, modelo.parametros)
    assert curva[0][1] == 1.0
    assert all(s1 <= s0 for (_, s0), (_, s1) in zip(curva, curva[1:]))
    # sobrevivência nunca negativa, ou seja, q'_x nunca passa de 1
    assert all(0 <= s <= 1 for _, s in curva)
    assert curva[-1][1] < 1e-6


def test_saidas_ficam_em_ordem(modelo):
    r = modelo.calcular(perfil(40))
    assert r.idade_atual < r.p10 < r.mediana < r.p90
    assert r.p10 < r.expectativa_media < r.p90


def test_risco_maior_encurta_a_faixa(modelo):
    tabua = modelo.tabua("feminino")
    baixo = calcular_resultado(tabua, 40, 0.8, modelo.parametros)
    alto = calcular_resultado(tabua, 40, 2.0, modelo.parametros)
    assert alto.expectativa_media < baixo.expectativa_media
    assert alto.p10 < baixo.p10 and alto.p90 < baixo.p90


# Valores do protótipo descrito no briefing (seção 7): homem de 38,4 anos,
# mesma curva provisória. Servem para confirmar que o núcleo novo reproduz o cálculo.
@pytest.mark.parametrize(
    "hr, media, p10, mediana, p90",
    [(1.0, 77.7, 59.2, 79.6, 92.9), (1.65, 72.8, 54.4, 74.0, 88.7)],
)
def test_reproduz_o_prototipo_do_briefing(modelo, hr, media, p10, mediana, p90):
    r = calcular_resultado(modelo.tabua("masculino"), 38.4, hr, modelo.parametros)
    assert r.expectativa_media == pytest.approx(media, abs=0.3)
    assert r.p10 == pytest.approx(p10, abs=0.3)
    assert r.mediana == pytest.approx(mediana, abs=0.3)
    assert r.p90 == pytest.approx(p90, abs=0.3)
