"""Exportar, importar e apagar a conta, com login de verdade."""

import io
import json
import zipfile

import pytest
from sqlmodel import Session, select

from app.modelos import Convite, Memoria, Usuario
from conftest import SENHA_ANA, SENHA_BIA, entrar, imagem


@pytest.fixture
def ana(servidor, pasta_fotos):
    """Ana com uma vida pequena: perfil, capítulo, duas memórias ligadas (uma com foto), intenção e respostas."""
    cliente = entrar(servidor())
    cliente.put("/api/perfil", json={"nascimento": "1990-03-14", "sexo": "feminino"})
    cliente.post("/api/capitulos", json={"nome": "Estúdio próprio", "inicio": "2018-11-05", "cor": "coral"})
    causa = cliente.post("/api/memorias", json={"data": "2018-06-29", "texto": "Pedi demissão.", "emocao": "incerteza"}).json()
    efeito = cliente.post("/api/memorias", json={"data": "2018-11-05", "texto": "Abri o estúdio.", "intensidade": 3,
                                                 "marcante": True, "veio_de": [causa["id"]]}).json()
    cliente.put(f"/api/memorias/{efeito['id']}/foto", files={"arquivo": ("f.jpg", imagem(400, 300), "image/jpeg")})
    cliente.post("/api/intencoes", json={"nome": "Abrir uma filial", "horizonte": {"tipo": "algum_dia"},
                                         "status": "virou_memoria", "memoria_id": efeito["id"]})
    cliente.post("/api/questionario/respostas", json={"respostas": {"sono": "menos_de_6"}})
    cliente.ids = {"causa": causa["id"], "efeito": efeito["id"]}
    return cliente


def abrir(conteudo: bytes) -> zipfile.ZipFile:
    return zipfile.ZipFile(io.BytesIO(conteudo))


def zip_de(dados: dict, extras: dict[str, bytes] | None = None) -> bytes:
    saida = io.BytesIO()
    with zipfile.ZipFile(saida, "w") as z:
        z.writestr("dados.json", json.dumps(dados))
        for nome, conteudo in (extras or {}).items():
            z.writestr(nome, conteudo)
    return saida.getvalue()


def importar(cliente, conteudo: bytes):
    return cliente.post("/api/importacao", files={"arquivo": ("dados.zip", conteudo, "application/zip")})


# ---------- exportar ----------

def test_exporta_tudo_num_zip_legivel(ana):
    r = ana.get("/api/exportacao")
    assert r.status_code == 200 and r.headers["content-type"] == "application/zip"
    assert 'filename="vida-em-semanas-' in r.headers["content-disposition"]

    z = abrir(r.content)
    dados = json.loads(z.read("dados.json"))
    assert dados["formato"] == 1 and dados["perfil"] == {"nascimento": "1990-03-14", "sexo": "feminino"}
    assert len(dados["memorias"]) == 2 and len(dados["capitulos"]) == 1 and len(dados["intencoes"]) == 1
    assert len(dados["respostas_de_saude"]) == 1
    assert f"fotos/{ana.ids['efeito']}.jpg" in z.namelist()

    texto = z.read("memorias.md").decode()
    assert "## Estúdio próprio (2018–hoje)" in texto and "Abri o estúdio." in texto
    assert texto.index("Pedi demissão.") < texto.index("## Estúdio próprio")


def test_exportar_marca_o_ultimo_backup(ana):
    assert ana.get("/api/perfil").json()["ultimo_backup"] is None
    ana.get("/api/exportacao")
    assert ana.get("/api/perfil").json()["ultimo_backup"] is not None


def test_exportacao_so_tem_os_dados_de_quem_pede(ana, servidor):
    bia = entrar(servidor(), "bia@exemplo.local", SENHA_BIA)
    dados = json.loads(abrir(bia.get("/api/exportacao").content).read("dados.json"))
    assert dados["memorias"] == [] and dados["respostas_de_saude"] == []


# ---------- importar ----------

def test_importar_em_outra_conta_recupera_tudo_sem_tocar_na_original(ana, servidor):
    pacote = ana.get("/api/exportacao").content
    bia = entrar(servidor(), "bia@exemplo.local", SENHA_BIA)

    r = importar(bia, pacote)
    assert r.status_code == 200, r.text
    assert r.json()["perfil_preenchido"] is True
    assert r.json()["resumo"]["memorias"]["criados"] == 2

    memorias = {m["texto"]: m for m in bia.get("/api/memorias").json()}
    efeito, causa = memorias["Abri o estúdio."], memorias["Pedi demissão."]
    assert efeito["id"] != ana.ids["efeito"]  # ids da Ana não são reaproveitados
    assert efeito["veio_de"] == [causa["id"]] and efeito["marcante"] is True
    assert bia.get(efeito["foto"]).status_code == 200
    assert bia.get("/api/intencoes").json()[0]["memoria_id"] == efeito["id"]
    assert bia.get("/api/capitulos").json()[0]["nome"] == "Estúdio próprio"
    assert bia.get("/api/estimativa").json()["base"] == "questionario"

    # a Ana continua igual, e cada uma só vê o que é seu
    assert sorted(m["id"] for m in ana.get("/api/memorias").json()) == sorted(ana.ids.values())
    assert bia.get(f"/api/memorias/{ana.ids['efeito']}").status_code == 404


def test_importar_de_novo_na_mesma_conta_nao_duplica(ana):
    pacote = ana.get("/api/exportacao").content
    r = importar(ana, pacote).json()
    assert r["resumo"]["memorias"] == {"criados": 0, "atualizados": 0, "mantidos": 2, "recusados": 0}
    assert len(ana.get("/api/memorias").json()) == 2
    assert len(ana.get("/api/questionario/respostas").json()) == 1


def test_versao_mais_nova_do_arquivo_atualiza(ana):
    dados = json.loads(abrir(ana.get("/api/exportacao").content).read("dados.json"))
    m = next(x for x in dados["memorias"] if x["id"] == ana.ids["causa"])
    m["texto"] = "Pedi demissão numa sexta-feira."
    m["atualizado_em"] = "2099-01-01T00:00:00+00:00"
    assert importar(ana, zip_de(dados)).json()["resumo"]["memorias"]["atualizados"] == 1
    assert ana.get(f"/api/memorias/{ana.ids['causa']}").json()["texto"] == "Pedi demissão numa sexta-feira."


def test_importar_traz_de_volta_memoria_excluida(ana):
    pacote = ana.get("/api/exportacao").content
    ana.delete(f"/api/memorias/{ana.ids['causa']}")
    importar(ana, pacote)
    assert ana.get(f"/api/memorias/{ana.ids['causa']}").status_code == 200


def test_ids_estranhos_no_arquivo_nunca_sao_usados(ana, servidor, pasta_fotos):
    dados = {"formato": 1, "perfil": {}, "capitulos": [], "intencoes": [], "respostas_de_saude": [],
             "memorias": [{"id": "../../fora", "data": "2020-01-01", "texto": "Id malicioso.",
                           "criado_em": "2020-01-01T00:00:00", "atualizado_em": "2020-01-01T00:00:00"}]}
    bia = entrar(servidor(), "bia@exemplo.local", SENHA_BIA)
    r = importar(bia, zip_de(dados, {"fotos/../../fora.jpg": imagem(50, 50)}))
    assert r.status_code == 200
    [m] = bia.get("/api/memorias").json()
    assert m["id"] != "../../fora" and len(m["id"]) == 32
    assert not (pasta_fotos.parent / "fora.jpg").exists()


def test_registros_invalidos_sao_recusados_um_a_um(ana):
    dados = {"formato": 1, "memorias": [
        {"id": "a" * 32, "data": "2999-01-01", "texto": "Do futuro."},
        {"id": "b" * 32, "data": "2020-01-01", "texto": "x" * 500},
        {"id": "c" * 32, "data": "2020-01-01", "texto": "Esta vale."},
    ]}
    r = importar(ana, zip_de(dados)).json()
    assert r["resumo"]["memorias"]["recusados"] == 2 and r["resumo"]["memorias"]["criados"] == 1


@pytest.mark.parametrize("conteudo, trecho", [
    (b"isto nao e um zip", "não é um ZIP"),
    (zip_de({"formato": 1}, None)[:10], "não é um ZIP"),
])
def test_arquivo_que_nao_e_zip(ana, conteudo, trecho):
    r = importar(ana, conteudo)
    assert r.status_code == 422 and trecho in r.json()["detail"]


def test_zip_sem_dados_ou_de_formato_desconhecido(ana):
    saida = io.BytesIO()
    with zipfile.ZipFile(saida, "w") as z:
        z.writestr("outra-coisa.txt", "oi")
    assert "dados.json" in importar(ana, saida.getvalue()).json()["detail"]
    assert importar(ana, zip_de({"formato": 99})).status_code == 422


def test_zip_que_se_expande_demais_e_recusado(ana, monkeypatch):
    from app import exportacao

    monkeypatch.setattr(exportacao, "TAMANHO_MAXIMO_DESCOMPACTADO", 1000)
    r = importar(ana, zip_de({"formato": 1, "memorias": []}, {"grande.txt": b"0" * 5000}))
    assert r.status_code == 422 and "grande demais" in r.json()["detail"]


# ---------- apagar a conta ----------

def test_apagar_conta_exige_a_senha(ana):
    assert ana.post("/api/conta/apagar", json={"senha": "errada-123456"}).status_code == 400
    assert ana.get("/api/memorias").status_code == 200


def test_apagar_conta_remove_tudo_de_verdade(ana, servidor, pasta_fotos):
    bia = entrar(servidor(), "bia@exemplo.local", SENHA_BIA)
    bia.post("/api/memorias", json={"data": "2020-01-01", "texto": "Da Bia."})
    ana.post("/api/admin/convites")
    outro_aparelho = entrar(servidor())
    assert (pasta_fotos / "ana").exists()

    assert ana.post("/api/conta/apagar", json={"senha": SENHA_ANA}).status_code == 204

    assert ana.get("/api/memorias").status_code == 401
    assert outro_aparelho.get("/api/conta").status_code == 401
    assert servidor().post("/api/entrar", json={"email": "ana@exemplo.local", "senha": SENHA_ANA}).status_code == 401
    assert not (pasta_fotos / "ana").exists()
    with Session(servidor.motor) as s:
        assert s.get(Usuario, "ana") is None
        assert s.exec(select(Memoria).where(Memoria.usuario_id == "ana")).all() == []
        assert s.exec(select(Convite)).all() == []
    # a Bia não perde nada
    assert [m["texto"] for m in bia.get("/api/memorias").json()] == ["Da Bia."]


def test_convite_usado_por_quem_apagou_a_conta_nao_volta_a_valer(servidor, pasta_fotos):
    admin = entrar(servidor())
    codigo = admin.post("/api/admin/convites").json()["caminho"].split("#convite-")[1]
    caio = servidor()
    caio.post("/api/contas", json={"codigo": codigo, "email": "caio@exemplo.local", "senha": "senha-do-caio-1"})
    assert caio.post("/api/conta/apagar", json={"senha": "senha-do-caio-1"}).status_code == 204
    r = servidor().post("/api/contas", json={"codigo": codigo, "email": "outro@exemplo.local", "senha": "senha-qualquer-1"})
    assert r.status_code == 400


def test_importar_duas_vezes_em_outra_conta_nao_duplica(ana, servidor):
    """Regressão: na conta nova os registros ganham ids novos; a segunda importação precisa reconhecê-los."""
    pacote = ana.get("/api/exportacao").content
    bia = entrar(servidor(), "bia@exemplo.local", SENHA_BIA)
    importar(bia, pacote)
    segunda = importar(bia, pacote).json()["resumo"]
    assert all(n["criados"] == 0 for n in segunda.values()), segunda
    assert len(bia.get("/api/memorias").json()) == 2
    assert len(bia.get("/api/capitulos").json()) == 1
    assert len(bia.get("/api/intencoes").json()) == 1
    assert len(bia.get("/api/questionario/respostas").json()) == 1
    efeito = next(m for m in bia.get("/api/memorias").json() if m["veio_de"])
    assert len(efeito["veio_de"]) == 1  # a ligação continua apontando para a mesma memória


def test_versao_nova_atualiza_tambem_na_conta_que_importou(ana, servidor):
    dados = json.loads(abrir(ana.get("/api/exportacao").content).read("dados.json"))
    bia = entrar(servidor(), "bia@exemplo.local", SENHA_BIA)
    importar(bia, zip_de(dados))
    m = next(x for x in dados["memorias"] if x["id"] == ana.ids["causa"])
    m["texto"], m["atualizado_em"] = "Texto novo.", "2099-01-01T00:00:00+00:00"
    assert importar(bia, zip_de(dados)).json()["resumo"]["memorias"]["atualizados"] == 1
    assert "Texto novo." in [x["texto"] for x in bia.get("/api/memorias").json()]
