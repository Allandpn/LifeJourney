"""Uma pessoa nunca consegue ver, alterar, apagar nem apontar para dados de outra.

Para cada tipo de registro, Ana cria um e Bia tenta todas as operações.
A resposta para Bia é sempre a mesma de um registro que não existe.
"""

import pytest

from conftest import ANA, BIA

CRIAR = {
    "memorias": {"data": "2020-01-01", "texto": "Só da Ana."},
    "capitulos": {"nome": "Só da Ana", "inicio": "2020-01-01", "cor": "azul"},
    "intencoes": {"nome": "Só da Ana", "horizonte": {"tipo": "algum_dia"}},
}
ALTERAR = {
    "memorias": {"texto": "Alterado pela Bia."},
    "capitulos": {"nome": "Alterado pela Bia"},
    "intencoes": {"nome": "Alterado pela Bia"},
}


@pytest.mark.parametrize("recurso", CRIAR)
def test_outra_pessoa_nao_ve_nao_altera_nao_apaga(api, recurso):
    registro = api.post(f"/api/{recurso}", json=CRIAR[recurso], headers=ANA).json()
    endereco = f"/api/{recurso}/{registro['id']}"

    assert api.get(f"/api/{recurso}", headers=BIA).json() == []
    assert api.get(endereco, headers=BIA).status_code == 404
    assert api.patch(endereco, json=ALTERAR[recurso], headers=BIA).status_code == 404
    assert api.delete(endereco, headers=BIA).status_code == 404

    # nada mudou para a Ana
    original = api.get(endereco, headers=ANA)
    assert original.status_code == 200
    assert "Bia" not in str(original.json())


def test_registro_de_outra_pessoa_responde_igual_a_inexistente(api):
    registro = api.post("/api/memorias", json=CRIAR["memorias"], headers=ANA).json()
    de_outra = api.get(f"/api/memorias/{registro['id']}", headers=BIA)
    inexistente = api.get("/api/memorias/nao-existe", headers=BIA)
    assert (de_outra.status_code, de_outra.json()) == (inexistente.status_code, inexistente.json())


def test_nao_da_para_ligar_memoria_a_memoria_de_outra_pessoa(api):
    da_ana = api.post("/api/memorias", json=CRIAR["memorias"], headers=ANA).json()

    r = api.post("/api/memorias", json={"data": "2021-01-01", "texto": "Da Bia.", "veio_de": [da_ana["id"]]},
                 headers=BIA)
    assert r.status_code == 422

    da_bia = api.post("/api/memorias", json={"data": "2021-01-01", "texto": "Da Bia."}, headers=BIA).json()
    assert api.patch(f"/api/memorias/{da_bia['id']}", json={"veio_de": [da_ana["id"]]},
                     headers=BIA).status_code == 422


def test_ligacao_de_outra_pessoa_nao_aparece_em_levou_a(api):
    """Mesmo que um id estranho fosse parar em veio_de, 'levou_a' só olha memórias do dono."""
    da_ana = api.post("/api/memorias", json=CRIAR["memorias"], headers=ANA).json()
    api.post("/api/memorias", json={"data": "2021-01-01", "texto": "Da Bia."}, headers=BIA)
    assert api.get(f"/api/memorias/{da_ana['id']}", headers=ANA).json()["levou_a"] == []


def test_nao_da_para_ligar_intencao_a_memoria_de_outra_pessoa(api):
    da_ana = api.post("/api/memorias", json=CRIAR["memorias"], headers=ANA).json()
    r = api.post("/api/intencoes", json={**CRIAR["intencoes"], "memoria_id": da_ana["id"]}, headers=BIA)
    assert r.status_code == 422


def test_perfil_e_de_cada_um(api):
    api.put("/api/perfil", json={"nascimento": "1990-03-14", "sexo": "feminino"}, headers=ANA)
    assert api.get("/api/perfil", headers=BIA).json()["nascimento"] is None


def test_id_enviado_pelo_aplicativo_e_ignorado(api):
    """O aplicativo não escolhe id nem dono: campos extras são recusados."""
    r = api.post("/api/memorias", json={**CRIAR["memorias"], "usuario_id": "bia"}, headers=ANA)
    assert r.status_code == 422
    r = api.post("/api/memorias", json={**CRIAR["memorias"], "id": "escolhido"}, headers=ANA)
    assert r.status_code == 422
