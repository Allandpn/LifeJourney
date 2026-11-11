"""Calibração contra Li et al., Circulation 2018 (resumo: PMID 29712712).

O artigo compara quem tem os 5 hábitos saudáveis (nunca fumar, IMC 18,5–24,9, ≥30 min/dia
de atividade, álcool moderado, dieta de qualidade) com quem não tem nenhum. A razão de
risco de morte foi 0,26 (IC 95%: 0,22–0,31).

Por que comparar a razão de risco, e não os anos de vida:
- os anos dependem da mortalidade de base (o artigo usa a dos EUA; nós, a do Brasil);
- a razão é exatamente o que o nosso modelo controla.

Por que o perfil "sem hábitos" é o típico, e não o extremo:
- o grupo do estudo reúne quem falha em cada critério (inclui sobrepeso, pouca atividade,
  pouco ou nenhum álcool), não quem está no pior ponto de todos.

Limites conhecidos:
- o questionário não tem dieta, e o modelo não dá benefício ao álcool moderado (por ser
  conservador); por isso a razão esperada é um pouco ACIMA de 0,26, e a margem de cima
  vai até 0,40;
- o grupo do estudo mistura fumantes e ex-fumantes, numa proporção que só o texto completo
  diria; o teste usa o fumante, e com ex-fumante a razão do modelo seria 0,51.
"""

import pytest

SAUDAVEL = {"tabagismo": "nunca", "imc": "20_a_25", "atividade": "150_a_300", "alcool": "ate_7"}
TIPICO_SEM_HABITOS = {"tabagismo": "fuma", "imc": "27_5_a_30", "atividade": "30_a_150", "alcool": "ate_7"}
EXTREMO = {"tabagismo": "fuma", "imc": "30_a_35", "atividade": "menos_de_30", "alcool": "25_ou_mais"}

RAZAO_DO_ESTUDO = 0.26
MARGEM = (0.22, 0.40)  # IC do estudo, alargado para cima por faltarem dieta e álcool moderado


@pytest.mark.parametrize("sexo", ["masculino", "feminino"])
def test_razao_de_risco_saudavel_contra_sem_habitos_bate_com_li_et_al(modelo, sexo):
    razao = modelo.hr_total(sexo, SAUDAVEL) / modelo.hr_total(sexo, TIPICO_SEM_HABITOS)
    assert MARGEM[0] <= razao <= MARGEM[1], f"razão {razao:.2f}, estudo {RAZAO_DO_ESTUDO}"


def test_perfil_extremo_fica_preso_no_teto(modelo):
    """O perfil extremo não serve para calibrar, mas confere que o teto segura riscos absurdos."""
    assert modelo.hr_total("masculino", EXTREMO) == modelo.parametros.hr_maximo
