import shutil
import sqlite3
import subprocess

import pytest

from app.copia import ErroDeCopia, fazer, restaurar

pytestmark = pytest.mark.skipif(not shutil.which("age"), reason="programa 'age' não instalado")


@pytest.fixture
def dados(tmp_path):
    banco = tmp_path / "vivo" / "lifejourney.db"
    banco.parent.mkdir()
    with sqlite3.connect(banco) as c:
        c.execute("create table memoria (texto text)")
        c.execute("insert into memoria values ('Abri o estúdio.')")
    fotos = tmp_path / "vivo" / "fotos" / "ana"
    fotos.mkdir(parents=True)
    (fotos / "abc-12345678.jpg").write_bytes(b"\xff\xd8 foto")
    chave = tmp_path / "chave.txt"
    subprocess.run(["age-keygen", "-o", str(chave)], check=True, capture_output=True)
    publica = next(l.split(": ")[1] for l in chave.read_text().splitlines() if "public key" in l)
    return {"banco": banco, "fotos": tmp_path / "vivo" / "fotos", "chave": chave, "publica": publica, "tmp": tmp_path}


def test_cria_copia_cifrada_e_restaura(dados):
    copia = fazer(dados["banco"], dados["fotos"], dados["tmp"] / "copias", dados["publica"])
    conteudo = copia.read_bytes()
    assert conteudo.startswith(b"age-encryption.org/v1")
    assert b"Abri o est" not in conteudo and b"foto" not in conteudo

    pasta = restaurar(copia, dados["chave"], dados["tmp"] / "restaurada")
    with sqlite3.connect(pasta / "lifejourney.db") as c:
        assert c.execute("select texto from memoria").fetchone() == ("Abri o estúdio.",)
    assert (pasta / "fotos" / "ana" / "abc-12345678.jpg").read_bytes() == b"\xff\xd8 foto"


def test_sem_a_chave_certa_nao_abre(dados):
    copia = fazer(dados["banco"], dados["fotos"], dados["tmp"] / "copias", dados["publica"])
    outra = dados["tmp"] / "outra.txt"
    subprocess.run(["age-keygen", "-o", str(outra)], check=True, capture_output=True)
    with pytest.raises(ErroDeCopia, match="decifrar"):
        restaurar(copia, outra, dados["tmp"] / "x")


def test_mantem_so_as_mais_recentes(dados, monkeypatch):
    import app.copia as modulo

    momentos = iter(["20260101-000000", "20260102-000000", "20260103-000000"])

    class Relogio:
        @staticmethod
        def now():
            class Data:
                def __format__(self, _):
                    return next(momentos)
            return Data()

    monkeypatch.setattr(modulo, "datetime", Relogio)
    destino = dados["tmp"] / "copias"
    for _ in range(3):
        fazer(dados["banco"], dados["fotos"], destino, dados["publica"], manter=2)
    assert sorted(p.name for p in destino.iterdir()) == [
        "vida-em-semanas-20260102-000000.tar.gz.age", "vida-em-semanas-20260103-000000.tar.gz.age"]


def test_recusa_sem_chave_publica_e_nao_sobrescreve_pasta_com_dados(dados):
    with pytest.raises(ErroDeCopia, match="age1"):
        fazer(dados["banco"], dados["fotos"], dados["tmp"] / "copias", "")
    copia = fazer(dados["banco"], dados["fotos"], dados["tmp"] / "copias", dados["publica"])
    with pytest.raises(ErroDeCopia, match="não está vazia"):
        restaurar(copia, dados["chave"], dados["banco"].parent)
