from conftest import ANA, BIA


def test_estimativa_exige_perfil(api):
    assert api.get("/api/estimativa", headers=ANA).status_code == 409


def test_estimativa_do_perfil(api):
    api.put("/api/perfil", json={"nascimento": "1990-03-14", "sexo": "feminino"}, headers=ANA)
    e = api.get("/api/estimativa", headers=ANA).json()

    assert e["base"] == "brasileiro_medio" and e["hr_total"] == 1.0
    assert e["p10"] < e["mediana"] < e["p90"]
    idades = [x for x, _ in e["sobrevivencia"]]
    chances = [s for _, s in e["sobrevivencia"]]
    assert chances[0] == 1.0 and chances == sorted(chances, reverse=True)
    assert all(abs((b - a) - 1) < 1e-6 for a, b in zip(idades, idades[1:]))


def test_estimativa_usa_o_perfil_de_quem_pede(api):
    api.put("/api/perfil", json={"nascimento": "1950-01-01", "sexo": "masculino"}, headers=ANA)
    api.put("/api/perfil", json={"nascimento": "2000-01-01", "sexo": "feminino"}, headers=BIA)
    ana = api.get("/api/estimativa", headers=ANA).json()
    bia = api.get("/api/estimativa", headers=BIA).json()
    assert ana["mediana"] != bia["mediana"]
