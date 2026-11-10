from datetime import date, timedelta

from conftest import ANA


def nova(api, **campos):
    dados = {"data": "2018-11-05", "texto": "Abri o estúdio.", **campos}
    resposta = api.post("/api/memorias", json=dados, headers=ANA)
    assert resposta.status_code == 201, resposta.text
    return resposta.json()


def test_cria_e_lista_memorias_em_ordem_de_data(api):
    nova(api, data="2020-03-17", texto="Quarentena.")
    nova(api, data="2001-02-05", texto="Mudança para Curitiba.", emocao="saudade", intensidade=3)

    lista = api.get("/api/memorias", headers=ANA).json()

    assert [m["texto"] for m in lista] == ["Mudança para Curitiba.", "Quarentena."]
    assert lista[0]["emocao"] == "saudade" and lista[0]["intensidade"] == 3
    assert lista[1]["intensidade"] == 2 and lista[1]["silenciar"] is False


def test_filtra_por_periodo(api):
    for ano in (2001, 2010, 2020):
        nova(api, data=f"{ano}-06-01")
    lista = api.get("/api/memorias?de=2005-01-01&ate=2015-12-31", headers=ANA).json()
    assert [m["data"] for m in lista] == ["2010-06-01"]


def test_recusa_memoria_no_futuro_ou_texto_longo(api):
    amanha = (date.today() + timedelta(days=1)).isoformat()
    assert api.post("/api/memorias", json={"data": amanha, "texto": "x"}, headers=ANA).status_code == 422
    longo = {"data": "2020-01-01", "texto": "x" * 281}
    assert api.post("/api/memorias", json=longo, headers=ANA).status_code == 422
    vazio = {"data": "2020-01-01", "texto": "   "}
    assert api.post("/api/memorias", json=vazio, headers=ANA).status_code == 422


def test_recusa_campos_desconhecidos_e_valores_fora_da_lista(api):
    base = {"data": "2020-01-01", "texto": "x"}
    assert api.post("/api/memorias", json={**base, "humor": "bom"}, headers=ANA).status_code == 422
    assert api.post("/api/memorias", json={**base, "emocao": "raiva"}, headers=ANA).status_code == 422
    assert api.post("/api/memorias", json={**base, "intensidade": 5}, headers=ANA).status_code == 422


def test_alteracao_que_deixa_a_memoria_invalida_e_recusada(api):
    m = nova(api)
    amanha = (date.today() + timedelta(days=1)).isoformat()
    resposta = api.patch(f"/api/memorias/{m['id']}", json={"data": amanha}, headers=ANA)
    assert resposta.status_code == 422
    assert api.get(f"/api/memorias/{m['id']}", headers=ANA).json()["data"] == m["data"]


def test_altera_so_os_campos_enviados(api):
    m = nova(api, emocao="orgulho", intensidade=3)
    resposta = api.patch(f"/api/memorias/{m['id']}", json={"silenciar": True}, headers=ANA)

    assert resposta.status_code == 200
    alterada = resposta.json()
    assert alterada["silenciar"] is True
    assert alterada["emocao"] == "orgulho" and alterada["intensidade"] == 3
    assert alterada["atualizado_em"] > m["atualizado_em"]


def test_ligacao_veio_de_e_levou_a(api):
    causa = nova(api, data="2018-06-29", texto="Pedi demissão.")
    efeito = nova(api, veio_de=[causa["id"]])

    assert efeito["veio_de"] == [causa["id"]]
    assert api.get(f"/api/memorias/{causa['id']}", headers=ANA).json()["levou_a"] == [efeito["id"]]


def test_recusa_ligacao_para_memoria_inexistente_ou_para_si_mesma(api):
    assert api.post("/api/memorias", json={"data": "2020-01-01", "texto": "x", "veio_de": ["nao-existe"]},
                    headers=ANA).status_code == 422
    m = nova(api)
    assert api.patch(f"/api/memorias/{m['id']}", json={"veio_de": [m["id"]]}, headers=ANA).status_code == 422


def test_excluir_esconde_a_memoria_e_as_ligacoes_para_ela(api):
    causa = nova(api, texto="Causa.")
    efeito = nova(api, veio_de=[causa["id"]])

    assert api.delete(f"/api/memorias/{causa['id']}", headers=ANA).status_code == 204

    assert api.get(f"/api/memorias/{causa['id']}", headers=ANA).status_code == 404
    assert [m["id"] for m in api.get("/api/memorias", headers=ANA).json()] == [efeito["id"]]
    assert api.get(f"/api/memorias/{efeito['id']}", headers=ANA).json()["veio_de"] == []
