"""Núcleo de cálculo: estimativa da faixa de vida a partir da tábua e dos fatores.

Tudo aqui é cálculo puro: não conhece banco de dados, login nem tela.
Os números do modelo vêm de `dados/fatores.json`; nenhum fica escrito no código.

Uso típico:

    from app.nucleo import carregar_modelo, Perfil
    modelo = carregar_modelo()
    resultado = modelo.calcular(Perfil(nascimento, "masculino", hoje), respostas)
"""

from app.nucleo.modelo import Modelo, Perfil, carregar_modelo
from app.nucleo.sobrevivencia import Resultado

__all__ = ["Modelo", "Perfil", "Resultado", "carregar_modelo"]
