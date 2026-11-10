from fastapi import APIRouter, Response, status

from app.api.dependencias import CapitulosDep, juntar_mudancas, obter_ou_404
from app.esquemas import CapituloDados, CapituloLido, CapituloMudancas
from app.modelos import Capitulo

rotas = APIRouter(prefix="/api/capitulos", tags=["capítulos"])


@rotas.get("", response_model=list[CapituloLido])
def listar_capitulos(capitulos: CapitulosDep):
    """Capítulos em ordem de início."""
    return capitulos.listar(ordem=Capitulo.inicio)


@rotas.post("", response_model=CapituloLido, status_code=status.HTTP_201_CREATED)
def criar_capitulo(dados: CapituloDados, capitulos: CapitulosDep):
    return capitulos.criar(dados.model_dump())


@rotas.get("/{id}", response_model=CapituloLido)
def ler_capitulo(id: str, capitulos: CapitulosDep):
    return obter_ou_404(capitulos, id)


@rotas.patch("/{id}", response_model=CapituloLido)
def alterar_capitulo(id: str, mudancas: CapituloMudancas, capitulos: CapitulosDep):
    """Altera só os campos enviados. Envie `"fim": null` para reabrir um capítulo."""
    atual = obter_ou_404(capitulos, id)
    return capitulos.atualizar(atual, juntar_mudancas(CapituloDados, atual, mudancas).model_dump())


@rotas.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def excluir_capitulo(id: str, capitulos: CapitulosDep):
    capitulos.excluir(obter_ou_404(capitulos, id))
    return Response(status_code=status.HTTP_204_NO_CONTENT)
