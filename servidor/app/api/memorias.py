from datetime import date

from fastapi import APIRouter, HTTPException, Response, status

from app.api.dependencias import MemoriasDep, exigir_memorias, juntar_mudancas, obter_ou_404
from app.esquemas import MemoriaDados, MemoriaLida, MemoriaMudancas
from app.modelos import Memoria

rotas = APIRouter(prefix="/api/memorias", tags=["memórias"])


def _ler(memorias: list[Memoria], todas: list[Memoria]) -> list[MemoriaLida]:
    """Monta a resposta: esconde ligações para memórias excluídas e calcula 'levou_a'."""
    ativas = {m.id for m in todas}
    levou_a: dict[str, list[str]] = {}
    for m in todas:
        for origem in m.veio_de:
            levou_a.setdefault(origem, []).append(m.id)
    return [
        MemoriaLida.model_validate(m).model_copy(update={
            "veio_de": [i for i in m.veio_de if i in ativas],
            "levou_a": levou_a.get(m.id, []),
        })
        for m in memorias
    ]


@rotas.get("", response_model=list[MemoriaLida])
def listar_memorias(memorias: MemoriasDep, de: date | None = None, ate: date | None = None):
    """Memórias em ordem de data. `de` e `ate` limitam o período (inclusive)."""
    condicoes = []
    if de:
        condicoes.append(Memoria.data >= de)
    if ate:
        condicoes.append(Memoria.data <= ate)
    escolhidas = memorias.listar(*condicoes, ordem=Memoria.data)
    return _ler(escolhidas, memorias.listar())


@rotas.post("", response_model=MemoriaLida, status_code=status.HTTP_201_CREATED)
def criar_memoria(dados: MemoriaDados, memorias: MemoriasDep):
    exigir_memorias(memorias, dados.veio_de, "veio_de")
    nova = memorias.criar(dados.model_dump())
    return _ler([nova], memorias.listar())[0]


@rotas.get("/{id}", response_model=MemoriaLida)
def ler_memoria(id: str, memorias: MemoriasDep):
    return _ler([obter_ou_404(memorias, id)], memorias.listar())[0]


@rotas.patch("/{id}", response_model=MemoriaLida)
def alterar_memoria(id: str, mudancas: MemoriaMudancas, memorias: MemoriasDep):
    """Altera só os campos enviados."""
    atual = obter_ou_404(memorias, id)
    dados = juntar_mudancas(MemoriaDados, atual, mudancas)
    if id in dados.veio_de:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "Uma memória não pode vir de si mesma.")
    exigir_memorias(memorias, dados.veio_de, "veio_de")
    alterada = memorias.atualizar(atual, dados.model_dump())
    return _ler([alterada], memorias.listar())[0]


@rotas.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def excluir_memoria(id: str, memorias: MemoriasDep):
    memorias.excluir(obter_ou_404(memorias, id))
    return Response(status_code=status.HTTP_204_NO_CONTENT)
