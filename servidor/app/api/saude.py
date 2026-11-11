"""Questionário de saúde, faixa estimada e "e se?".

Respostas de saúde são dados sensíveis: ficam isoladas por dono como todo o resto
e, quando a pessoa pede, são apagadas de verdade do banco.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel, ConfigDict, Field

from app.api.dependencias import SessaoDep, UsuarioDep
from app.modelos import RespostasDeSaude, Usuario
from app.nucleo import Perfil, carregar_modelo
from app.nucleo.modelo import Modelo
from app.repositorio import Repositorio

rotas = APIRouter(prefix="/api", tags=["estimativa e questionário"])


def _respostas(sessao: SessaoDep, usuario: UsuarioDep) -> Repositorio[RespostasDeSaude]:
    return Repositorio(sessao, usuario.id, RespostasDeSaude)


RespostasDep = Annotated[Repositorio[RespostasDeSaude], Depends(_respostas)]


# ---------- formatos ----------

class Opcao(BaseModel):
    valor: str
    rotulo: str


class Pergunta(BaseModel):
    fator: str
    pergunta: str
    tipo: str  # "opcoes" ou "altura_e_peso"
    opcoes: list[Opcao]
    fonte: str
    muda_com_habito: bool  # tem "e se?"


class EnvioDeRespostas(BaseModel):
    model_config = ConfigDict(extra="forbid")

    respostas: dict[str, str] = Field(default_factory=dict, description="Fator -> resposta. Perguntas puladas ficam de fora.")
    altura_m: float | None = Field(default=None, ge=1.0, le=2.5)
    peso_kg: float | None = Field(default=None, ge=25, le=350)


class Mudanca(BaseModel):
    fator: str  # ou "todas"
    acao: str  # ex.: "Dormir de 6 a 8 horas"
    hr_total: float
    ganho_semanas: float
    mediana: float


class EstimativaLida(BaseModel):
    """Faixa estimada de vida, em idades (anos)."""

    base: str  # "brasileiro_medio" ou "questionario"
    respondido_em: date | None
    versao_config: str
    hr_total: float
    expectativa_media: float
    p10: float
    mediana: float
    p90: float
    sobrevivencia: list[tuple[float, float]]  # (idade, chance de estar vivo), um ponto por ano
    e_se: list[Mudanca]


class RespostasLidas(BaseModel):
    id: str
    criado_em: datetime
    respostas: dict[str, str]
    altura_m: float | None
    peso_kg: float | None
    resultado: dict


# ---------- cálculo ----------

def _perfil(usuario: Usuario) -> Perfil:
    if usuario.nascimento is None or usuario.sexo is None:
        raise HTTPException(status.HTTP_409_CONFLICT, "Preencha a data de nascimento e o sexo no perfil.")
    return Perfil(usuario.nascimento, usuario.sexo, date.today())


def _validar(modelo: Modelo, envio: EnvioDeRespostas) -> dict[str, str]:
    """Confere as respostas contra a configuração e transforma altura e peso em faixa de IMC."""
    fatores = modelo.config["fatores"]
    respostas = dict(envio.respostas)
    if "imc" in respostas:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "O IMC é calculado da altura e do peso.")
    for fator, resposta in respostas.items():
        if fator not in fatores:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, f"Pergunta desconhecida: {fator}.")
        if resposta not in fatores[fator]["respostas"]:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, f"Resposta inválida para {fator}.")
    if (envio.altura_m is None) != (envio.peso_kg is None):
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "Informe a altura e o peso, ou nenhum dos dois.")
    if envio.altura_m is not None:
        respostas["imc"] = modelo.categoria_imc(envio.altura_m, envio.peso_kg)
    return respostas


def _estimativa(modelo: Modelo, perfil: Perfil, ultimas: RespostasDeSaude | None) -> EstimativaLida:
    # respostas de uma versão antiga da configuração podem citar algo que não existe mais
    fatores = modelo.config["fatores"]
    respostas = {f: r for f, r in (ultimas.respostas if ultimas else {}).items()
                 if f in fatores and r in fatores[f]["respostas"]}
    r = modelo.calcular(perfil, respostas)
    passos = modelo.parametros.passos_por_ano
    mudancas = [
        Mudanca(fator=m.fator, acao=fatores[m.fator].get("acao_e_se", m.fator) if m.fator != "todas" else "Todas juntas",
                hr_total=m.hr_total, ganho_semanas=m.ganho_semanas, mediana=m.resultado.mediana)
        for m in modelo.e_se(perfil, respostas)
    ]
    return EstimativaLida(
        base="questionario" if ultimas else "brasileiro_medio",
        respondido_em=ultimas.criado_em.date() if ultimas else None,
        versao_config=modelo.versao, hr_total=r.hr_total, expectativa_media=r.expectativa_media,
        p10=r.p10, mediana=r.mediana, p90=r.p90,
        sobrevivencia=[(round(x, 3), round(s, 5)) for x, s in r.curva[::passos]],
        e_se=mudancas,
    )


def _ultimas(repositorio: Repositorio[RespostasDeSaude]) -> RespostasDeSaude | None:
    lista = repositorio.listar(ordem=RespostasDeSaude.criado_em.desc())
    return lista[0] if lista else None


# ---------- rotas ----------

@rotas.get("/questionario", response_model=list[Pergunta])
def perguntas():
    """As perguntas, na ordem, com as opções de resposta e a fonte de cada número."""
    modelo = carregar_modelo()
    lista = []
    for fator, f in modelo.config["fatores"].items():
        lista.append(Pergunta(
            fator=fator, pergunta=f["pergunta"], tipo="altura_e_peso" if fator == "imc" else "opcoes",
            opcoes=[Opcao(valor=v, rotulo=d["rotulo"]) for v, d in f["respostas"].items()],
            fonte=f["fonte"], muda_com_habito=bool(f.get("e_se")),
        ))
    return lista


@rotas.get("/estimativa", response_model=EstimativaLida)
def ler_estimativa(usuario: UsuarioDep, respostas: RespostasDep):
    """Faixa estimada para hoje: com as últimas respostas, ou a média brasileira se não houver."""
    return _estimativa(carregar_modelo(), _perfil(usuario), _ultimas(respostas))


@rotas.post("/questionario/respostas", response_model=EstimativaLida, status_code=status.HTTP_201_CREATED)
def responder(envio: EnvioDeRespostas, usuario: UsuarioDep, respostas: RespostasDep):
    """Guarda uma rodada de respostas e devolve a faixa nova."""
    modelo = carregar_modelo()
    perfil = _perfil(usuario)
    validas = _validar(modelo, envio)
    r = modelo.calcular(perfil, validas)
    nova = respostas.criar({
        "respostas": validas, "altura_m": envio.altura_m, "peso_kg": envio.peso_kg, "versao_config": modelo.versao,
        "resultado": {"idade": round(perfil.idade, 2), "hr_total": round(r.hr_total, 4),
                      "expectativa_media": round(r.expectativa_media, 2), "p10": round(r.p10, 2),
                      "mediana": round(r.mediana, 2), "p90": round(r.p90, 2)},
    })
    return _estimativa(modelo, perfil, nova)


@rotas.get("/questionario/respostas", response_model=list[RespostasLidas])
def historico(respostas: RespostasDep):
    """Rodadas anteriores, da mais nova para a mais antiga."""
    return [RespostasLidas.model_validate(r, from_attributes=True)
            for r in respostas.listar(ordem=RespostasDeSaude.criado_em.desc())]


@rotas.delete("/questionario/respostas", status_code=status.HTTP_204_NO_CONTENT)
def apagar_respostas(respostas: RespostasDep):
    """Apaga de verdade todas as respostas de saúde desta conta. A faixa volta à média brasileira."""
    respostas.apagar_de_vez(respostas.listar())
    return Response(status_code=status.HTTP_204_NO_CONTENT)
