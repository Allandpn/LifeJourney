"""Peças compartilhadas pelos testes."""

import copy
from datetime import date
from pathlib import Path

import pytest

from app.nucleo import Perfil, carregar_modelo
from app.nucleo.configuracao import ler_json
from app.nucleo.modelo import Modelo

RAIZ_DO_REPOSITORIO = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="session")
def modelo() -> Modelo:
    """Modelo com a configuração real (dados/fatores.json)."""
    return carregar_modelo()


@pytest.fixture
def config_real() -> dict:
    """Cópia da configuração real, para os testes poderem alterar à vontade."""
    return copy.deepcopy(ler_json())


@pytest.fixture
def config_simples(config_real) -> dict:
    """Configuração com dois fatores de números redondos, para testar as regras.

    - "causal_a": causal, média brasileira 1,25
    - "marcador_b": marcador, média brasileira 2,0
    """
    config_real["fatores"] = {
        "causal_a": {
            "pergunta": "A?", "bloco": "causal", "fonte": "teste",
            "respostas": {"bom": {"hr": 1.0}, "medio": {"hr": 1.25}, "ruim": {"hr": 2.5}},
            "media_br": {"valor": 1.25},
            "e_se": {"ruim": "bom", "medio": "bom"},
        },
        "marcador_b": {
            "pergunta": "B?", "bloco": "marcador", "fonte": "teste",
            "respostas": {"bom": {"hr": 1.0}, "ruim": {"hr": 4.0}},
            "media_br": {"valor": 2.0},
        },
    }
    return config_real


def perfil(idade_anos: int = 40, sexo: str = "masculino") -> Perfil:
    """Perfil fictício com a idade pedida em 1º de janeiro de 2026."""
    return Perfil(date(2026 - idade_anos, 1, 1), sexo, date(2026, 1, 1))


def modelo_de(config: dict) -> Modelo:
    return Modelo(config, Path(__file__).resolve().parents[1] / "dados")


# ---------- API ----------

from fastapi import Header  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402
from sqlmodel import Session, select  # noqa: E402

from app.api.dependencias import usuario_atual  # noqa: E402
from app.banco import criar_motor, criar_tabelas, obter_sessao  # noqa: E402
from app.modelos import Usuario  # noqa: E402
from app.principal import app as aplicacao  # noqa: E402


@pytest.fixture
def api():
    """Cliente da API com banco em memória e dois usuários fictícios.

    O cabeçalho `X-Teste-Usuario` escolhe quem faz a requisição ("ana" ou "bia").
    Ele só existe nos testes; o login de verdade entra na etapa 5.
    """
    motor = criar_motor("sqlite://", poolclass=StaticPool)
    criar_tabelas(motor)
    with Session(motor) as sessao:
        sessao.add(Usuario(id="ana", email="ana@exemplo.local"))
        sessao.add(Usuario(id="bia", email="bia@exemplo.local"))
        sessao.commit()

    def sessao_de_teste():
        with Session(motor) as sessao:
            yield sessao

    def usuario_de_teste(x_teste_usuario: str = Header("ana")):
        with Session(motor) as sessao:
            return sessao.exec(select(Usuario).where(Usuario.id == x_teste_usuario)).one()

    aplicacao.dependency_overrides[obter_sessao] = sessao_de_teste
    aplicacao.dependency_overrides[usuario_atual] = usuario_de_teste
    yield TestClient(aplicacao)
    aplicacao.dependency_overrides.clear()


ANA = {"X-Teste-Usuario": "ana"}
BIA = {"X-Teste-Usuario": "bia"}


@pytest.fixture
def pasta_fotos(tmp_path):
    """Pasta temporária para as fotos dos testes."""
    from app.config import Configuracao, obter_configuracao

    pasta = tmp_path / "fotos"
    aplicacao.dependency_overrides[obter_configuracao] = lambda: Configuracao(
        modo="desenvolvimento", caminho_banco=tmp_path / "nao-usado.db", pasta_fotos=pasta,
        email_desenvolvimento="dev@exemplo.local",
    )
    return pasta


def imagem(largura: int = 3000, altura: int = 2000, formato: str = "JPEG", exif: bool = False) -> bytes:
    """Uma imagem de teste. Com `exif`, leva uma marca de GPS e uma rotação."""
    import io

    from PIL import Image

    img = Image.new("RGB", (largura, altura), (200, 80, 60))
    saida = io.BytesIO()
    if exif:
        dados = Image.Exif()
        dados[0x0112] = 6  # orientação: girar 90°
        dados[0x8825] = {1: "S", 2: (23.0, 33.0, 0.0)}  # GPS
        img.save(saida, formato, exif=dados.tobytes())
    else:
        img.save(saida, formato)
    return saida.getvalue()
