from conftest import modelo_de, perfil


def test_e_se_mostra_so_o_que_pode_melhorar(modelo):
    respostas = {"tabagismo": "nunca", "sono": "menos_de_6", "depressao": "sim", "caminhada": "lento"}
    mudancas = modelo.e_se(perfil(40), respostas)
    # tabagismo já é o melhor; depressão e caminhada não têm "e se"; sobra só o sono
    assert [m.fator for m in mudancas] == ["sono"]
    assert mudancas[0].alternativa == "6_a_8"
    assert mudancas[0].ganho_semanas > 0


def test_pergunta_pulada_nao_gera_e_se(modelo):
    assert modelo.e_se(perfil(40), {}) == []


def test_todas_juntas_ganham_mais_que_cada_uma(modelo):
    respostas = {"sono": "menos_de_6", "vinculos": "nenhuma", "imc": "27_5_a_30"}
    mudancas = modelo.e_se(perfil(40), respostas)
    assert mudancas[-1].fator == "todas"
    individuais = [m.ganho_semanas for m in mudancas[:-1]]
    assert individuais == sorted(individuais, reverse=True)
    assert mudancas[-1].ganho_semanas > max(individuais)


def test_ganho_e_a_diferenca_na_expectativa_em_semanas(config_simples):
    m = modelo_de(config_simples)
    p = perfil(40)
    [mudanca] = m.e_se(p, {"causal_a": "ruim"})
    antes = m.calcular(p, {"causal_a": "ruim"}).expectativa_media
    depois = m.calcular(p, {"causal_a": "bom"}).expectativa_media
    assert mudanca.ganho_semanas == (depois - antes) * 52.1775
