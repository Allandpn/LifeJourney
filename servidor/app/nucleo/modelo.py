"""Junta tábua, fatores e parâmetros num único objeto fácil de usar."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from functools import lru_cache
from pathlib import Path

from app.nucleo import configuracao
from app.nucleo.fatores import Fator, categoria_imc, hr_combinado, ler_fatores
from app.nucleo.sobrevivencia import Resultado, calcular_resultado
from app.nucleo.tabua import SEXOS, Tabua, carregar_tabua

DIAS_POR_ANO = 365.2425


@dataclass(frozen=True)
class Perfil:
    nascimento: date
    sexo: str  # "masculino" ou "feminino"
    data_calculo: date

    @property
    def idade(self) -> float:
        """Idade exata em anos fracionários."""
        dias = (self.data_calculo - self.nascimento).days
        if dias < 0:
            raise ValueError("A data do cálculo é anterior ao nascimento.")
        return dias / DIAS_POR_ANO


@dataclass(frozen=True)
class Mudanca:
    """Uma simulação de "e se?"."""

    fator: str  # chave do fator, ou "todas" para todas as mudanças juntas
    resposta_atual: str | None
    alternativa: str | None
    hr_total: float
    resultado: Resultado
    ganho_semanas: float  # diferença na expectativa média, em semanas


@dataclass
class Modelo:
    config: dict
    pasta_dados: Path
    parametros: configuracao.Parametros = field(init=False)
    _tabuas: dict[str, Tabua] = field(init=False, default_factory=dict)
    _fatores: dict[str, dict[str, Fator]] = field(init=False, default_factory=dict)

    def __post_init__(self) -> None:
        self.parametros = configuracao.ler_parametros(self.config)

    @property
    def versao(self) -> str:
        return self.config["versao"]

    def tabua(self, sexo: str) -> Tabua:
        if sexo not in self._tabuas:
            self._tabuas[sexo] = carregar_tabua(
                self.config["tabua"], sexo, int(self.parametros.idade_maxima), self.pasta_dados
            )
        return self._tabuas[sexo]

    def fatores(self, sexo: str) -> dict[str, Fator]:
        """Fatores com os HRs já resolvidos (os dados em "anos perdidos" dependem da tábua)."""
        if sexo not in self._fatores:
            self._fatores[sexo] = ler_fatores(
                self.config, lambda anos, idade: self.hr_para_perda(sexo, anos, idade)
            )
        return self._fatores[sexo]

    def hr_para_perda(self, sexo: str, anos: float, idade: float) -> float:
        """HR que, aplicado na idade dada, tira `anos` da expectativa média.

        Usado para estudos que publicam o efeito em anos de vida, e não em HR
        (álcool, em Wood et al. 2018).
        """
        if anos <= 0:
            return 1.0
        base = calcular_resultado(self.tabua(sexo), idade, 1.0, self.parametros).expectativa_media
        baixo, alto = 1.0, self.parametros.hr_maximo * 4
        for _ in range(60):
            meio = (baixo + alto) / 2
            perda = base - calcular_resultado(self.tabua(sexo), idade, meio, self.parametros).expectativa_media
            if perda < anos:
                baixo = meio
            else:
                alto = meio
        return (baixo + alto) / 2

    def categoria_imc(self, altura_m: float, peso_kg: float) -> str:
        return categoria_imc(altura_m, peso_kg, self.config["fatores"]["imc"]["faixas"])

    def hr_total(self, sexo: str, respostas: dict[str, str]) -> float:
        return hr_combinado(self.fatores(sexo), respostas, self.parametros)

    def calcular(self, perfil: Perfil, respostas: dict[str, str] | None = None) -> Resultado:
        """Faixa estimada para o perfil. Respostas ausentes contam como a média brasileira."""
        if perfil.sexo not in SEXOS:
            raise ValueError(f"Sexo deve ser um de {SEXOS}.")
        hr = self.hr_total(perfil.sexo, respostas or {})
        return calcular_resultado(self.tabua(perfil.sexo), perfil.idade, hr, self.parametros)

    def e_se(self, perfil: Perfil, respostas: dict[str, str]) -> list[Mudanca]:
        """Ganho de cada mudança possível nos fatores causais, e de todas juntas.

        Só entram fatores com alternativa definida em `e_se` na configuração e
        cuja resposta atual tenha uma alternativa mais saudável.
        """
        atual = self.calcular(perfil, respostas)
        semanas = self.parametros.semanas_por_ano
        mudancas: list[Mudanca] = []
        todas = dict(respostas)
        for chave, fator in self.fatores(perfil.sexo).items():
            resposta = respostas.get(chave)
            alternativa = fator.e_se.get(resposta) if resposta else None
            if not alternativa:
                continue
            todas[chave] = alternativa
            nova = {**respostas, chave: alternativa}
            resultado = self.calcular(perfil, nova)
            mudancas.append(Mudanca(
                fator=chave, resposta_atual=resposta, alternativa=alternativa,
                hr_total=resultado.hr_total, resultado=resultado,
                ganho_semanas=(resultado.expectativa_media - atual.expectativa_media) * semanas,
            ))
        mudancas.sort(key=lambda m: m.ganho_semanas, reverse=True)
        if len(mudancas) > 1:
            resultado = self.calcular(perfil, todas)
            mudancas.append(Mudanca(
                fator="todas", resposta_atual=None, alternativa=None,
                hr_total=resultado.hr_total, resultado=resultado,
                ganho_semanas=(resultado.expectativa_media - atual.expectativa_media) * semanas,
            ))
        return mudancas


@lru_cache(maxsize=4)
def _modelo_em_cache(caminho: str) -> Modelo:
    caminho_path = Path(caminho)
    return Modelo(configuracao.ler_json(caminho_path), caminho_path.parent)


def carregar_modelo(caminho: Path | str = configuracao.ARQUIVO_PADRAO) -> Modelo:
    """Carrega o modelo a partir do arquivo de configuração (padrão: dados/fatores.json)."""
    return _modelo_em_cache(str(Path(caminho).resolve()))
