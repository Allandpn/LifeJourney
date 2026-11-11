import pytest

from conftest import ANA, BIA

RISCO = {"tabagismo": "fuma", "sono": "menos_de_6", "vinculos": "nenhuma", "depressao": "sim"}


@pytest.fixture
def com_perfil(api):
    for quem in (ANA, BIA):
        api.put("/api/perfil", json={"nascimento": "1988-06-08", "sexo": "masculino"}, headers=quem)
    return api


def responder(api, quem=ANA, **envio):
    r = api.post("/api/questionario/respostas", json=envio, headers=quem)
    assert r.status_code == 201, r.text
    return r.json()


def test_perguntas_tem_rotulos_e_a_de_imc_pede_altura_e_peso(api):
    perguntas = api.get("/api/questionario", headers=ANA).json()
    assert len(perguntas) == 10
    imc = next(p for p in perguntas if p["fator"] == "imc")
    assert imc["tipo"] == "altura_e_peso"
    fumo = next(p for p in perguntas if p["fator"] == "tabagismo")
    assert {"valor": "fuma", "rotulo": "fumo"} in fumo["opcoes"] and fumo["muda_com_habito"]
    assert not next(p for p in perguntas if p["fator"] == "depressao")["muda_com_habito"]


def test_sem_respostas_a_estimativa_e_a_media_brasileira(com_perfil):
    e = com_perfil.get("/api/estimativa", headers=ANA).json()
    assert e["base"] == "brasileiro_medio" and e["respondido_em"] is None
    assert e["hr_total"] == 1.0 and e["e_se"] == []


def test_responder_muda_a_estimativa(com_perfil):
    antes = com_perfil.get("/api/estimativa", headers=ANA).json()
    depois = responder(com_perfil, respostas=RISCO, altura_m=1.88, peso_kg=97)

    assert depois["base"] == "questionario" and depois["respondido_em"]
    assert depois["hr_total"] > 1 and depois["mediana"] < antes["mediana"]
    assert com_perfil.get("/api/estimativa", headers=ANA).json()["mediana"] == pytest.approx(depois["mediana"])


def test_e_se_tem_frase_e_ganho_em_semanas(com_perfil):
    e = responder(com_perfil, respostas=RISCO, altura_m=1.88, peso_kg=97)
    fatores = [m["fator"] for m in e["e_se"]]
    assert set(fatores[:-1]) == {"tabagismo", "sono", "vinculos", "imc"}  # depressão não é hábito
    assert fatores[-1] == "todas"
    sono = next(m for m in e["e_se"] if m["fator"] == "sono")
    assert sono["acao"] == "Dormir de 6 a 8 horas" and sono["ganho_semanas"] > 0


def test_altura_e_peso_viram_faixa_de_imc(com_perfil):
    responder(com_perfil, respostas={}, altura_m=1.88, peso_kg=97)
    [rodada] = com_perfil.get("/api/questionario/respostas", headers=ANA).json()
    assert rodada["respostas"] == {"imc": "25_a_27_5"}
    assert rodada["altura_m"] == 1.88 and rodada["peso_kg"] == 97


def test_pular_tudo_da_a_media_brasileira(com_perfil):
    e = responder(com_perfil, respostas={})
    assert e["hr_total"] == 1.0 and e["base"] == "questionario"


@pytest.mark.parametrize("envio", [
    {"respostas": {"signo": "leao"}},
    {"respostas": {"tabagismo": "as_vezes"}},
    {"respostas": {"imc": "20_a_25"}},
    {"respostas": {}, "altura_m": 1.80},
    {"respostas": {}, "altura_m": 3.5, "peso_kg": 80},
    {"respostas": {}, "altura_m": 1.80, "peso_kg": 5},
    {"respostas": {}, "humor": "bom"},
])
def test_respostas_invalidas_sao_recusadas(com_perfil, envio):
    assert com_perfil.post("/api/questionario/respostas", json=envio, headers=ANA).status_code == 422


def test_historico_da_mais_nova_para_a_mais_antiga(com_perfil):
    responder(com_perfil, respostas={"sono": "menos_de_6"})
    responder(com_perfil, respostas={"sono": "6_a_8"})
    historico = com_perfil.get("/api/questionario/respostas", headers=ANA).json()
    assert [h["respostas"]["sono"] for h in historico] == ["6_a_8", "menos_de_6"]
    assert {"hr_total", "mediana", "p10", "p90", "idade"} <= set(historico[0]["resultado"])


def test_estimativa_usa_a_rodada_mais_recente(com_perfil):
    responder(com_perfil, respostas=RISCO)
    ultima = responder(com_perfil, respostas={"tabagismo": "nunca"})
    assert com_perfil.get("/api/estimativa", headers=ANA).json()["hr_total"] == pytest.approx(ultima["hr_total"])


def test_apagar_respostas_remove_de_verdade_e_volta_a_media(com_perfil):
    from sqlmodel import select

    from app.modelos import RespostasDeSaude

    responder(com_perfil, respostas=RISCO)
    assert com_perfil.delete("/api/questionario/respostas", headers=ANA).status_code == 204
    assert com_perfil.get("/api/questionario/respostas", headers=ANA).json() == []
    assert com_perfil.get("/api/estimativa", headers=ANA).json()["base"] == "brasileiro_medio"
    # saiu do banco, não ficou só marcado como excluído
    from app.banco import obter_sessao
    from app.principal import app
    sessao = next(app.dependency_overrides[obter_sessao]())
    assert sessao.exec(select(RespostasDeSaude)).all() == []


def test_respostas_de_saude_sao_de_cada_um(com_perfil):
    responder(com_perfil, respostas=RISCO)
    assert com_perfil.get("/api/questionario/respostas", headers=BIA).json() == []
    assert com_perfil.get("/api/estimativa", headers=BIA).json()["base"] == "brasileiro_medio"
    # apagar as da Bia não apaga as da Ana
    com_perfil.delete("/api/questionario/respostas", headers=BIA)
    assert len(com_perfil.get("/api/questionario/respostas", headers=ANA).json()) == 1


def test_questionario_exige_perfil(api):
    assert api.post("/api/questionario/respostas", json={"respostas": {}}, headers=ANA).status_code == 409


def test_respostas_de_versao_antiga_da_configuracao_sao_ignoradas(com_perfil):
    """Se a configuração mudar e uma resposta deixar de existir, a estimativa não quebra."""
    from sqlmodel import select

    from app.banco import obter_sessao
    from app.modelos import RespostasDeSaude
    from app.principal import app

    responder(com_perfil, respostas={"sono": "menos_de_6"})
    sessao = next(app.dependency_overrides[obter_sessao]())
    rodada = sessao.exec(select(RespostasDeSaude)).one()
    rodada.respostas = {"sono": "resposta_que_sumiu", "fator_que_sumiu": "x"}
    sessao.add(rodada)
    sessao.commit()
    assert com_perfil.get("/api/estimativa", headers=ANA).json()["hr_total"] == 1.0
