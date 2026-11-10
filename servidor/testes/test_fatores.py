import math

import pytest

from conftest import modelo_de, perfil


def test_sem_respostas_o_risco_e_o_do_brasileiro_medio(modelo):
    assert modelo.hr_total("masculino", {}) == 1.0


def test_resposta_igual_a_media_brasileira_nao_muda_o_risco(config_simples):
    m = modelo_de(config_simples)
    assert m.hr_total("masculino", {"causal_a": "medio"}) == pytest.approx(1.0)


def test_fator_causal_entra_dividido_pela_media(config_simples):
    m = modelo_de(config_simples)
    assert m.hr_total("masculino", {"causal_a": "ruim"}) == pytest.approx(2.5 / 1.25)


def test_marcador_entra_com_peso_reduzido(config_simples):
    m = modelo_de(config_simples)
    # exp(0,5 · ln(4 / 2)) = raiz de 2
    assert m.hr_total("masculino", {"marcador_b": "ruim"}) == pytest.approx(math.sqrt(2))


def test_fatores_se_combinam_multiplicando(config_simples):
    m = modelo_de(config_simples)
    total = m.hr_total("masculino", {"causal_a": "ruim", "marcador_b": "ruim"})
    assert total == pytest.approx(2.0 * math.sqrt(2))


def test_risco_total_respeita_teto_e_piso(config_simples):
    config_simples["fatores"]["causal_a"]["respostas"]["pessimo"] = {"hr": 50}
    config_simples["fatores"]["causal_a"]["respostas"]["otimo"] = {"hr": 0.01}
    m = modelo_de(config_simples)
    assert m.hr_total("masculino", {"causal_a": "pessimo"}) == 4.0
    assert m.hr_total("masculino", {"causal_a": "otimo"}) == 0.4


def test_media_brasileira_pode_vir_das_prevalencias(config_simples):
    config_simples["fatores"]["causal_a"]["media_br"] = {
        "prevalencias": {"bom": 0.5, "medio": 0.3, "ruim": 0.2}
    }
    m = modelo_de(config_simples)
    media = 0.5 * 1.0 + 0.3 * 1.25 + 0.2 * 2.5
    assert m.fatores("masculino")["causal_a"].media_br == pytest.approx(media)
    assert m.hr_total("masculino", {"causal_a": "ruim"}) == pytest.approx(2.5 / media)


def test_prevalencias_precisam_somar_1(config_simples):
    config_simples["fatores"]["causal_a"]["media_br"] = {"prevalencias": {"bom": 0.5, "ruim": 0.2}}
    with pytest.raises(ValueError, match="somam"):
        modelo_de(config_simples).fatores("masculino")


def test_fator_ou_resposta_desconhecidos_sao_recusados(modelo):
    with pytest.raises(ValueError, match="desconhecidos"):
        modelo.hr_total("masculino", {"signo": "leao"})
    with pytest.raises(ValueError, match="não existe"):
        modelo.hr_total("masculino", {"tabagismo": "as_vezes"})


@pytest.mark.parametrize(
    "altura, peso, esperado",
    [(1.80, 58, "abaixo_de_18_5"), (1.80, 70, "20_a_25"), (1.88, 97, "25_a_27_5"),
     (1.70, 86.7, "30_a_35"), (1.60, 110, "40_ou_mais")],
)
def test_categoria_de_imc(modelo, altura, peso, esperado):
    assert modelo.categoria_imc(altura, peso) == esperado


def test_imc_no_limite_vai_para_a_faixa_de_cima(modelo):
    assert modelo.categoria_imc(1.0, 25.0) == "25_a_27_5"


def test_perda_em_anos_vira_hr_que_reproduz_a_perda(modelo):
    hr = modelo.hr_para_perda("masculino", 4.0, 40)
    base = modelo.calcular(perfil(40)).expectativa_media
    from app.nucleo.sobrevivencia import calcular_resultado

    com_perda = calcular_resultado(modelo.tabua("masculino"), 40, hr, modelo.parametros)
    assert base - com_perda.expectativa_media == pytest.approx(4.0, abs=0.01)


def test_mais_alcool_significa_mais_risco(modelo):
    hrs = modelo.fatores("feminino")["alcool"].hrs
    assert hrs["ate_7"] < hrs["7_a_14"] < hrs["14_a_25"] < hrs["25_ou_mais"]
