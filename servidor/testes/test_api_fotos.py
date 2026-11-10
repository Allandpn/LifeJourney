import io

from PIL import Image

from conftest import ANA, BIA, imagem


def memoria(api):
    return api.post("/api/memorias", json={"data": "2020-01-01", "texto": "Com foto."}, headers=ANA).json()


def enviar(api, id, conteudo, quem=ANA, nome="foto.jpg"):
    return api.put(f"/api/memorias/{id}/foto", files={"arquivo": (nome, conteudo, "image/jpeg")}, headers=quem)


def test_envia_reduz_e_devolve_a_foto(api, pasta_fotos):
    m = memoria(api)
    r = enviar(api, m["id"], imagem(4000, 3000))
    assert r.status_code == 200, r.text
    assert r.json()["foto"].startswith(f"/api/memorias/{m['id']}/foto?v=")

    foto = api.get(r.json()["foto"], headers=ANA)
    assert foto.status_code == 200 and foto.headers["content-type"] == "image/jpeg"
    assert "private" in foto.headers["cache-control"]
    assert max(Image.open(io.BytesIO(foto.content)).size) == 1600


def test_apaga_metadados_e_aplica_a_rotacao(api, pasta_fotos):
    m = memoria(api)
    enviar(api, m["id"], imagem(400, 200, exif=True))
    foto = Image.open(io.BytesIO(api.get(f"/api/memorias/{m['id']}/foto", headers=ANA).content))
    assert len(foto.getexif()) == 0
    assert foto.size == (200, 400)  # a rotação foi aplicada antes de descartar o EXIF


def test_aceita_png_e_guarda_como_jpeg(api, pasta_fotos):
    m = memoria(api)
    assert enviar(api, m["id"], imagem(300, 300, "PNG"), nome="foto.png").status_code == 200
    assert api.get(f"/api/memorias/{m['id']}/foto", headers=ANA).content[:2] == b"\xff\xd8"


def test_recusa_arquivo_que_nao_e_imagem(api, pasta_fotos):
    m = memoria(api)
    r = enviar(api, m["id"], b"%PDF-1.4 isto nao e uma foto")
    assert r.status_code == 422
    assert api.get(f"/api/memorias/{m['id']}", headers=ANA).json()["foto"] is None


def test_recusa_arquivo_grande_demais(api, pasta_fotos):
    m = memoria(api)
    assert enviar(api, m["id"], b"\xff" * (15 * 1024 * 1024 + 10)).status_code == 413


def test_trocar_a_foto_apaga_a_anterior(api, pasta_fotos):
    m = memoria(api)
    primeira = enviar(api, m["id"], imagem(300, 300)).json()["foto"]
    segunda = enviar(api, m["id"], imagem(500, 300)).json()["foto"]
    assert primeira != segunda
    assert len(list((pasta_fotos / "ana").iterdir())) == 1


def test_remove_a_foto(api, pasta_fotos):
    m = memoria(api)
    enviar(api, m["id"], imagem(300, 300))
    r = api.delete(f"/api/memorias/{m['id']}/foto", headers=ANA)
    assert r.status_code == 200 and r.json()["foto"] is None
    assert list((pasta_fotos / "ana").iterdir()) == []
    assert api.get(f"/api/memorias/{m['id']}/foto", headers=ANA).status_code == 404


def test_editar_o_texto_mantem_a_foto(api, pasta_fotos):
    m = memoria(api)
    enviar(api, m["id"], imagem(300, 300))
    r = api.patch(f"/api/memorias/{m['id']}", json={"texto": "Outro texto."}, headers=ANA)
    assert r.json()["foto"] is not None


def test_outra_pessoa_nao_ve_nao_troca_nao_apaga_a_foto(api, pasta_fotos):
    m = memoria(api)
    enviar(api, m["id"], imagem(300, 300))
    assert api.get(f"/api/memorias/{m['id']}/foto", headers=BIA).status_code == 404
    assert enviar(api, m["id"], imagem(300, 300), quem=BIA).status_code == 404
    assert api.delete(f"/api/memorias/{m['id']}/foto", headers=BIA).status_code == 404
    assert api.get(f"/api/memorias/{m['id']}/foto", headers=ANA).status_code == 200


def test_fotos_ficam_em_pastas_separadas_por_dono(api, pasta_fotos):
    m = memoria(api)
    enviar(api, m["id"], imagem(300, 300))
    assert [p.name for p in pasta_fotos.iterdir()] == ["ana"]


def test_nomes_de_arquivo_fora_do_padrao_sao_recusados(tmp_path):
    import pytest

    from app import fotos

    for nome in ["../x.jpg", "abc.jpg", "a-12345678.png", "a-12345678.jpg/../../x"]:
        with pytest.raises(ValueError):
            fotos.caminho(tmp_path, "ana", nome)
    assert fotos.caminho(tmp_path, "ana", "abc123-0a1b2c3d.jpg") == tmp_path / "ana" / "abc123-0a1b2c3d.jpg"
