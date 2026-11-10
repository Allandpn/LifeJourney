"""Caso de teste com dados reais, guardado fora do git.

O arquivo `dados-pessoais/caso-teste.json` (na raiz do repositório) não é
versionado, porque contém dados de saúde. Sem ele, este teste é pulado.
O formato está em `testes/caso-pessoal.exemplo.json`.
"""

import json
from datetime import date

import pytest

from app.nucleo import Perfil
from conftest import RAIZ_DO_REPOSITORIO

ARQUIVO = RAIZ_DO_REPOSITORIO / "dados-pessoais" / "caso-teste.json"


@pytest.fixture(scope="module")
def caso() -> dict:
    if not ARQUIVO.exists():
        pytest.skip("Sem dados-pessoais/caso-teste.json (fica fora do git).")
    return json.loads(ARQUIVO.read_text(encoding="utf-8"))


def _perfil(caso: dict) -> Perfil:
    p = caso["perfil"]
    return Perfil(
        date.fromisoformat(p["nascimento"]), p["sexo"], date.fromisoformat(p["data_calculo"])
    )


def _respostas(modelo, caso: dict) -> dict:
    respostas = dict(caso["respostas"])
    if "altura_m" in caso["perfil"]:
        respostas["imc"] = modelo.categoria_imc(caso["perfil"]["altura_m"], caso["perfil"]["peso_kg"])
    return respostas


def test_caso_pessoal_bate_com_o_esperado(modelo, caso):
    esperado = caso["esperado"]
    tolerancia = caso.get("tolerancia_anos", 0.5)
    r = modelo.calcular(_perfil(caso), _respostas(modelo, caso))

    assert r.hr_total == pytest.approx(esperado["hr_total"], abs=0.02)
    for campo in ("expectativa_media", "p10", "mediana", "p90"):
        assert getattr(r, campo) == pytest.approx(esperado[campo], abs=tolerancia), campo


def test_e_se_do_caso_pessoal(modelo, caso):
    esperado = caso.get("e_se", {})
    if not esperado:
        pytest.skip("Caso sem valores de 'e se'.")
    tolerancia = caso.get("tolerancia_semanas", 5)
    mudancas = {m.fator: m for m in modelo.e_se(_perfil(caso), _respostas(modelo, caso))}
    for fator, valores in esperado.items():
        assert mudancas[fator].hr_total == pytest.approx(valores["hr_total"], abs=0.02), fator
        assert mudancas[fator].ganho_semanas == pytest.approx(valores["ganho_semanas"], abs=tolerancia), fator
