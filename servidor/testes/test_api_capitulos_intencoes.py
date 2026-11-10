from conftest import ANA


def test_cria_capitulo_em_andamento_e_depois_fecha(api):
    dados = {"nome": "Estúdio próprio", "inicio": "2018-11-05", "cor": "coral"}
    criado = api.post("/api/capitulos", json=dados, headers=ANA).json()
    assert criado["fim"] is None and criado["principal"] is True

    fechado = api.patch(f"/api/capitulos/{criado['id']}", json={"fim": "2024-12-31"}, headers=ANA).json()
    assert fechado["fim"] == "2024-12-31"

    reaberto = api.patch(f"/api/capitulos/{criado['id']}", json={"fim": None}, headers=ANA).json()
    assert reaberto["fim"] is None


def test_capitulos_saem_em_ordem_de_inicio(api):
    for nome, inicio in [("Faculdade", "2008-03-01"), ("Infância", "1990-03-14")]:
        api.post("/api/capitulos", json={"nome": nome, "inicio": inicio, "cor": "azul"}, headers=ANA)
    assert [c["nome"] for c in api.get("/api/capitulos", headers=ANA).json()] == ["Infância", "Faculdade"]


def test_recusa_capitulo_que_termina_antes_de_comecar_ou_cor_fora_da_paleta(api):
    errado = {"nome": "X", "inicio": "2020-01-01", "fim": "2019-01-01", "cor": "azul"}
    assert api.post("/api/capitulos", json=errado, headers=ANA).status_code == 422
    cor = {"nome": "X", "inicio": "2020-01-01", "cor": "vermelho"}
    assert api.post("/api/capitulos", json=cor, headers=ANA).status_code == 422
    criado = api.post("/api/capitulos", json={"nome": "X", "inicio": "2020-01-01", "cor": "azul"}, headers=ANA).json()
    assert api.patch(f"/api/capitulos/{criado['id']}", json={"fim": "2019-01-01"}, headers=ANA).status_code == 422


def test_intencao_com_os_tres_tipos_de_horizonte(api):
    horizontes = [
        {"tipo": "data", "data": "2027-04-01"},
        {"tipo": "intervalo", "de": "2027-01-01", "ate": "2028-12-31"},
        {"tipo": "algum_dia"},
    ]
    for h in horizontes:
        r = api.post("/api/intencoes", json={"nome": "Plano", "horizonte": h}, headers=ANA)
        assert r.status_code == 201, r.text
        assert r.json()["horizonte"] == h and r.json()["status"] == "ativa"


def test_recusa_horizonte_invalido(api):
    for h in [{"tipo": "intervalo", "de": "2028-01-01", "ate": "2027-01-01"},
              {"tipo": "data"}, {"tipo": "logo"}]:
        assert api.post("/api/intencoes", json={"nome": "X", "horizonte": h}, headers=ANA).status_code == 422


def test_intencao_vira_memoria(api):
    intencao = api.post("/api/intencoes", json={"nome": "Meia maratona", "horizonte": {"tipo": "algum_dia"}},
                        headers=ANA).json()
    memoria = api.post("/api/memorias", json={"data": "2024-06-02", "texto": "Corri a meia."}, headers=ANA).json()

    r = api.patch(f"/api/intencoes/{intencao['id']}", json={"status": "virou_memoria", "memoria_id": memoria["id"]},
                  headers=ANA)

    assert r.status_code == 200
    assert r.json()["status"] == "virou_memoria" and r.json()["memoria_id"] == memoria["id"]
    assert r.json()["horizonte"] == {"tipo": "algum_dia"}


def test_status_concluido_nao_existe(api):
    r = api.post("/api/intencoes", json={"nome": "X", "horizonte": {"tipo": "algum_dia"}, "status": "concluida"},
                 headers=ANA)
    assert r.status_code == 422


def test_perfil(api):
    assert api.get("/api/perfil", headers=ANA).json()["nascimento"] is None
    r = api.put("/api/perfil", json={"nascimento": "1990-03-14", "sexo": "feminino"}, headers=ANA)
    assert r.status_code == 200
    assert api.get("/api/perfil", headers=ANA).json() == {
        "email": "ana@exemplo.local", "nascimento": "1990-03-14", "sexo": "feminino", "ultimo_backup": None,
    }
    assert api.put("/api/perfil", json={"nascimento": "2999-01-01", "sexo": "feminino"}, headers=ANA).status_code == 422
