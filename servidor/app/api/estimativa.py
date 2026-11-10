from datetime import date

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from app.api.dependencias import UsuarioDep
from app.nucleo import Perfil, carregar_modelo

rotas = APIRouter(prefix="/api/estimativa", tags=["estimativa"])


class EstimativaLida(BaseModel):
    """Faixa estimada de vida, em idades (anos)."""

    base: str  # "brasileiro_medio" até o questionário existir (etapa 6)
    versao_config: str
    hr_total: float
    expectativa_media: float
    p10: float
    mediana: float
    p90: float
    sobrevivencia: list[tuple[float, float]]  # (idade, chance de estar vivo), um ponto por ano


@rotas.get("", response_model=EstimativaLida)
def ler_estimativa(usuario: UsuarioDep):
    """Faixa estimada para o perfil de quem está logado.

    Por enquanto sem questionário: usa a média brasileira de mesmo sexo e idade.
    """
    if usuario.nascimento is None or usuario.sexo is None:
        raise HTTPException(status.HTTP_409_CONFLICT, "Preencha a data de nascimento e o sexo no perfil.")
    modelo = carregar_modelo()
    r = modelo.calcular(Perfil(usuario.nascimento, usuario.sexo, date.today()))
    passos = modelo.parametros.passos_por_ano
    anual = [(round(x, 3), round(s, 5)) for x, s in r.curva[::passos]]
    return EstimativaLida(
        base="brasileiro_medio", versao_config=modelo.versao, hr_total=r.hr_total,
        expectativa_media=r.expectativa_media, p10=r.p10, mediana=r.mediana, p90=r.p90,
        sobrevivencia=anual,
    )
