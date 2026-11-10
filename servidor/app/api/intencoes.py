from fastapi import APIRouter, Response, status

from app.api.dependencias import IntencoesDep, MemoriasDep, exigir_memorias, juntar_mudancas, obter_ou_404
from app.esquemas import IntencaoDados, IntencaoLida, IntencaoMudancas
from app.modelos import Intencao

rotas = APIRouter(prefix="/api/intencoes", tags=["intenções"])


@rotas.get("", response_model=list[IntencaoLida])
def listar_intencoes(intencoes: IntencoesDep):
    """Intenções, das mais antigas para as mais novas."""
    return intencoes.listar(ordem=Intencao.criado_em)


@rotas.post("", response_model=IntencaoLida, status_code=status.HTTP_201_CREATED)
def criar_intencao(dados: IntencaoDados, intencoes: IntencoesDep, memorias: MemoriasDep):
    if dados.memoria_id:
        exigir_memorias(memorias, [dados.memoria_id], "memoria_id")
    return intencoes.criar(dados.model_dump(mode="json"))


@rotas.get("/{id}", response_model=IntencaoLida)
def ler_intencao(id: str, intencoes: IntencoesDep):
    return obter_ou_404(intencoes, id)


@rotas.patch("/{id}", response_model=IntencaoLida)
def alterar_intencao(id: str, mudancas: IntencaoMudancas, intencoes: IntencoesDep, memorias: MemoriasDep):
    """Altera só os campos enviados. Para virar memória: `status` "virou_memoria" e `memoria_id`."""
    atual = obter_ou_404(intencoes, id)
    dados = juntar_mudancas(IntencaoDados, atual, mudancas)
    if dados.memoria_id:
        exigir_memorias(memorias, [dados.memoria_id], "memoria_id")
    return intencoes.atualizar(atual, dados.model_dump(mode="json"))


@rotas.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def excluir_intencao(id: str, intencoes: IntencoesDep):
    intencoes.excluir(obter_ou_404(intencoes, id))
    return Response(status_code=status.HTTP_204_NO_CONTENT)
