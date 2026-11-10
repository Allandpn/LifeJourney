"""Login, sessões, convites e senhas, sem atalhos de teste."""

from datetime import timedelta

from sqlmodel import Session, select

from app.modelos import Convite, Sessao, Usuario, agora
from conftest import SENHA_ANA, SENHA_BIA, entrar


# ---------- entrar e sair ----------

def test_entrar_cria_cookie_protegido_e_libera_os_dados(servidor):
    cliente = servidor()
    r = cliente.post("/api/entrar", json={"email": "ANA@exemplo.local ", "senha": SENHA_ANA})
    assert r.status_code == 200 and r.json() == {"email": "ana@exemplo.local", "administrador": True}
    cookie = r.headers["set-cookie"].lower()
    assert "httponly" in cookie and "samesite=lax" in cookie
    assert cliente.get("/api/memorias").status_code == 200


def test_senha_errada_e_email_inexistente_dao_a_mesma_resposta(servidor):
    cliente = servidor()
    errada = cliente.post("/api/entrar", json={"email": "ana@exemplo.local", "senha": "errada-123456"})
    inexistente = cliente.post("/api/entrar", json={"email": "ninguem@exemplo.local", "senha": "errada-123456"})
    assert errada.status_code == inexistente.status_code == 401
    assert errada.json() == inexistente.json()
    assert cliente.get("/api/memorias").status_code == 401


def test_muitos_erros_bloqueiam_aquele_email_por_um_tempo(servidor):
    cliente = servidor()
    for _ in range(5):
        cliente.post("/api/entrar", json={"email": "ana@exemplo.local", "senha": "errada-123456"})
    certa = cliente.post("/api/entrar", json={"email": "ana@exemplo.local", "senha": SENHA_ANA})
    assert certa.status_code == 429
    # outra conta não é afetada
    assert cliente.post("/api/entrar", json={"email": "bia@exemplo.local", "senha": SENHA_BIA}).status_code == 200


def test_sair_invalida_a_sessao_mesmo_que_o_cookie_seja_reaproveitado(servidor):
    cliente = entrar(servidor())
    cookie = cliente.cookies.get("lj_sessao")
    assert cliente.post("/api/sair").status_code == 204
    copia = servidor()
    copia.cookies.set("lj_sessao", cookie)
    assert copia.get("/api/memorias").status_code == 401


def test_cookie_inventado_nao_entra(servidor):
    cliente = servidor()
    cliente.cookies.set("lj_sessao", "inventado")
    assert cliente.get("/api/conta").status_code == 401


def test_sessao_vencida_nao_entra(servidor):
    cliente = entrar(servidor())
    with Session(servidor.motor) as s:
        for sessao in s.exec(select(Sessao)):
            sessao.expira_em = agora() - timedelta(seconds=1)
            s.add(sessao)
        s.commit()
    assert cliente.get("/api/conta").status_code == 401


def test_banco_guarda_so_hashes_nunca_a_senha_nem_o_codigo_da_sessao(servidor):
    cliente = entrar(servidor())
    codigo = cliente.cookies.get("lj_sessao")
    with Session(servidor.motor) as s:
        ana = s.get(Usuario, "ana")
        assert ana.senha_hash.startswith("$argon2") and SENHA_ANA not in ana.senha_hash
        assert all(codigo not in x.codigo_hash for x in s.exec(select(Sessao)))


# ---------- isolamento com sessões de verdade ----------

def test_cada_pessoa_so_ve_o_que_e_seu(servidor):
    ana = entrar(servidor())
    bia = entrar(servidor(), "bia@exemplo.local", SENHA_BIA)
    memoria = ana.post("/api/memorias", json={"data": "2020-01-01", "texto": "Só da Ana."}).json()

    assert bia.get("/api/memorias").json() == []
    assert bia.get(f"/api/memorias/{memoria['id']}").status_code == 404
    assert bia.delete(f"/api/memorias/{memoria['id']}").status_code == 404
    assert ana.get(f"/api/memorias/{memoria['id']}").status_code == 200


# ---------- aparelhos conectados e troca de senha ----------

def test_lista_e_desconecta_aparelhos(servidor):
    celular = entrar(servidor())
    computador = entrar(servidor())
    lista = celular.get("/api/conta/sessoes").json()
    assert len(lista) == 2 and sum(s["esta"] for s in lista) == 1

    outro = next(s for s in lista if not s["esta"])
    assert celular.delete(f"/api/conta/sessoes/{outro['id']}").status_code == 204
    assert computador.get("/api/conta").status_code == 401
    assert celular.get("/api/conta").status_code == 200


def test_nao_da_para_desconectar_aparelho_de_outra_pessoa(servidor):
    ana = entrar(servidor())
    bia = entrar(servidor(), "bia@exemplo.local", SENHA_BIA)
    da_ana = ana.get("/api/conta/sessoes").json()[0]["id"]
    assert bia.delete(f"/api/conta/sessoes/{da_ana}").status_code == 404
    assert ana.get("/api/conta").status_code == 200


def test_trocar_senha(servidor):
    celular = entrar(servidor())
    computador = entrar(servidor())
    nova = "uma-senha-nova-789"

    assert celular.post("/api/conta/senha", json={"senha_atual": "errada", "senha_nova": nova}).status_code == 400
    assert celular.post("/api/conta/senha", json={"senha_atual": SENHA_ANA, "senha_nova": "curta"}).status_code == 422
    assert celular.post("/api/conta/senha", json={"senha_atual": SENHA_ANA, "senha_nova": nova}).status_code == 204

    assert celular.get("/api/conta").status_code == 200  # este aparelho continua
    assert computador.get("/api/conta").status_code == 401  # os outros saem
    assert servidor().post("/api/entrar", json={"email": "ana@exemplo.local", "senha": SENHA_ANA}).status_code == 401
    entrar(servidor(), senha=nova)


# ---------- convites ----------

def _convite(admin):
    r = admin.post("/api/admin/convites")
    assert r.status_code == 201
    return r.json()["caminho"].split("#convite-")[1]


def test_convite_cria_conta_e_ja_entra(servidor):
    codigo = _convite(entrar(servidor()))
    nova = servidor()
    r = nova.post("/api/contas", json={"codigo": codigo, "email": "Caio@Exemplo.local", "senha": "senha-do-caio-1"})
    assert r.status_code == 201 and r.json() == {"email": "caio@exemplo.local", "administrador": False}
    assert nova.get("/api/memorias").json() == []


def test_convite_vale_uma_vez(servidor):
    codigo = _convite(entrar(servidor()))
    servidor().post("/api/contas", json={"codigo": codigo, "email": "caio@exemplo.local", "senha": "senha-do-caio-1"})
    r = servidor().post("/api/contas", json={"codigo": codigo, "email": "duda@exemplo.local", "senha": "senha-da-duda-1"})
    assert r.status_code == 400


def test_convite_vencido_cancelado_ou_inventado_nao_vale(servidor):
    admin = entrar(servidor())
    vencido = _convite(admin)
    cancelado = _convite(admin)
    with Session(servidor.motor) as s:
        primeiro = s.exec(select(Convite).order_by(Convite.criado_em)).first()
        primeiro.valido_ate = agora() - timedelta(seconds=1)
        s.add(primeiro)
        s.commit()
    id_cancelado = admin.get("/api/admin/convites").json()[0]["id"]
    assert admin.delete(f"/api/admin/convites/{id_cancelado}").status_code == 204

    for codigo in (vencido, cancelado, "inventado"):
        r = servidor().post("/api/contas", json={"codigo": codigo, "email": "x@exemplo.local", "senha": "senha-qualquer-1"})
        assert r.status_code == 400, codigo


def test_convite_recusa_email_repetido_e_senha_curta(servidor):
    codigo = _convite(entrar(servidor()))
    assert servidor().post("/api/contas", json={"codigo": codigo, "email": "bia@exemplo.local",
                                                "senha": "senha-qualquer-1"}).status_code == 409
    assert servidor().post("/api/contas", json={"codigo": codigo, "email": "novo@exemplo.local",
                                                "senha": "curta"}).status_code == 422


def test_so_o_administrador_cria_convites_e_redefinicoes(servidor):
    bia = entrar(servidor(), "bia@exemplo.local", SENHA_BIA)
    assert bia.post("/api/admin/convites").status_code == 403
    assert bia.get("/api/admin/convites").status_code == 403
    assert bia.post("/api/admin/redefinicoes", json={"email": "ana@exemplo.local"}).status_code == 403


def test_codigo_do_convite_nao_fica_no_banco(servidor):
    codigo = _convite(entrar(servidor()))
    with Session(servidor.motor) as s:
        assert all(codigo not in c.codigo_hash for c in s.exec(select(Convite)))


# ---------- redefinição de senha ----------

def test_redefinicao_troca_a_senha_e_desconecta_tudo(servidor):
    admin = entrar(servidor())
    aparelho_da_bia = entrar(servidor(), "bia@exemplo.local", SENHA_BIA)
    link = admin.post("/api/admin/redefinicoes", json={"email": "bia@exemplo.local"}).json()["caminho"]
    codigo = link.split("#redefinir-")[1]

    assert servidor().post("/api/redefinir-senha", json={"codigo": codigo, "senha_nova": "nova-da-bia-123"}).status_code == 204
    assert aparelho_da_bia.get("/api/conta").status_code == 401
    entrar(servidor(), "bia@exemplo.local", "nova-da-bia-123")
    # o link não vale de novo
    assert servidor().post("/api/redefinir-senha", json={"codigo": codigo, "senha_nova": "outra-senha-123"}).status_code == 400


def test_redefinicao_para_email_inexistente(servidor):
    admin = entrar(servidor())
    assert admin.post("/api/admin/redefinicoes", json={"email": "ninguem@exemplo.local"}).status_code == 404


def test_muitas_tentativas_de_codigo_sao_bloqueadas(servidor):
    cliente = servidor()
    respostas = [cliente.post("/api/contas", json={"codigo": f"chute-{i}", "email": "x@exemplo.local",
                                                   "senha": "senha-qualquer-1"}).status_code for i in range(22)]
    assert respostas[-1] == 429


# ---------- pedidos de outros sites ----------

def test_pedido_de_outro_site_e_recusado(servidor):
    cliente = entrar(servidor())
    r = cliente.post("/api/memorias", json={"data": "2020-01-01", "texto": "x"}, headers={"Origin": "https://malicioso.example"})
    assert r.status_code == 403
    r = cliente.post("/api/memorias", json={"data": "2020-01-01", "texto": "x"}, headers={"Origin": "http://testserver"})
    assert r.status_code == 201


def test_respostas_da_api_nao_ficam_em_cache_e_tem_cabecalhos_de_seguranca(servidor):
    r = entrar(servidor()).get("/api/memorias")
    assert r.headers["cache-control"] == "no-store"
    assert r.headers["x-content-type-options"] == "nosniff"
    assert r.headers["x-frame-options"] == "DENY"


# ---------- achados da revisão de segurança ----------

def test_adivinhar_a_senha_atual_tem_o_mesmo_limite_do_login(servidor):
    cliente = entrar(servidor())
    for _ in range(5):
        cliente.post("/api/conta/senha", json={"senha_atual": "chute-errado", "senha_nova": "qualquer-coisa-1"})
    r = cliente.post("/api/conta/senha", json={"senha_atual": SENHA_ANA, "senha_nova": "qualquer-coisa-1"})
    assert r.status_code == 429


def test_producao_nao_liga_com_a_senha_de_desenvolvimento(monkeypatch):
    import pytest
    from sqlalchemy.pool import StaticPool

    from app import principal
    from app.banco import criar_motor, criar_tabelas
    from app.config import Configuracao
    from app.exemplo import SENHA_DE_DESENVOLVIMENTO
    from app.seguranca import hash_da_senha

    motor = criar_motor("sqlite://", poolclass=StaticPool)
    criar_tabelas(motor)
    with Session(motor) as s:
        s.add(Usuario(email="dev@exemplo.local", senha_hash=hash_da_senha(SENHA_DE_DESENVOLVIMENTO)))
        s.commit()
    producao = Configuracao(modo="producao", caminho_banco=None, pasta_fotos=None, email_desenvolvimento="dev@exemplo.local")
    monkeypatch.setattr(principal, "obter_configuracao", lambda: producao)
    with pytest.raises(RuntimeError, match="senha de desenvolvimento"):
        principal.conferir_conta_de_desenvolvimento(motor)

    with Session(motor) as s:
        dev = s.exec(select(Usuario)).first()
        dev.senha_hash = hash_da_senha("outra-senha-forte")
        s.add(dev)
        s.commit()
    principal.conferir_conta_de_desenvolvimento(motor)  # com outra senha, liga normalmente
