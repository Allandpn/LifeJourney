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
