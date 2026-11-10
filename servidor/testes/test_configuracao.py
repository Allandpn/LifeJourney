"""Confere a qualidade do arquivo dados/fatores.json."""

STATUS_VALIDOS = {"publicado", "aproximado", "provisorio"}


def test_todo_fator_tem_pergunta_fonte_e_bloco_valido(config_real):
    for chave, fator in config_real["fatores"].items():
        assert "?" in fator["pergunta"], chave
        assert fator["fonte"], chave
        assert fator["bloco"] in {"causal", "marcador"}, chave


def test_toda_resposta_diz_o_grau_de_confianca(config_real):
    for chave, fator in config_real["fatores"].items():
        for resposta, definicao in fator["respostas"].items():
            assert definicao.get("status") in STATUS_VALIDOS, f"{chave}.{resposta}"


def test_marcadores_nao_tem_e_se_exceto_atividade(config_real):
    # o briefing só dá "e se" a fatores causais; atividade física é causal e marcador
    for chave, fator in config_real["fatores"].items():
        if fator["bloco"] == "marcador" and chave != "atividade":
            assert not fator.get("e_se"), chave


def test_toda_faixa_de_imc_tem_hr(config_real):
    imc = config_real["fatores"]["imc"]
    respostas = {f["resposta"] for f in imc["faixas"]} | {imc["faixas"][-1]["resposta_acima"]}
    assert respostas == set(imc["respostas"])


def test_configuracao_real_carrega_para_os_dois_sexos(modelo):
    for sexo in ("masculino", "feminino"):
        assert len(modelo.fatores(sexo)) == 10
