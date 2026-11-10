"""Calibração contra Li et al., Circulation 2018.

Aos 50 anos, quem tem os hábitos saudáveis deve viver perto de 12 anos (homens)
e 14 anos (mulheres) a mais que quem não tem nenhum. O nosso questionário não
tem dieta, então compara quatro dos cinco hábitos do artigo.

Hoje o modelo passa do alvo; a calibração (redutor, teto e piso) é uma
pendência de docs/05-modelo-de-calculo.md. O teste fica marcado como falha
esperada: quando a calibração estiver feita, ele passa e o pytest avisa.
"""

import pytest

from conftest import perfil

SAUDAVEL = {"tabagismo": "nunca", "imc": "20_a_25", "atividade": "150_a_300", "alcool": "ate_7"}
NENHUM = {"tabagismo": "fuma", "imc": "30_a_35", "atividade": "menos_de_30", "alcool": "25_ou_mais"}


@pytest.mark.xfail(reason="Calibração pendente: hoje a diferença passa de 16 anos.", strict=True)
@pytest.mark.parametrize("sexo, alvo", [("masculino", 12), ("feminino", 14)])
def test_diferenca_entre_perfis_extremos_aos_50(modelo, sexo, alvo):
    p = perfil(50, sexo)
    diferenca = (
        modelo.calcular(p, SAUDAVEL).expectativa_media
        - modelo.calcular(p, NENHUM).expectativa_media
    )
    assert diferenca == pytest.approx(alvo, abs=2)
