from datetime import date

from fastapi import APIRouter, HTTPException, Response, UploadFile, status
from fastapi.responses import FileResponse

from app import fotos
from app.api.dependencias import ConfigDep, MemoriasDep, exigir_memorias, juntar_mudancas, obter_ou_404
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
            # o nome do arquivo muda a cada envio, o que obriga o navegador a buscar a foto nova
            "foto": f"/api/memorias/{m.id}/foto?v={m.foto_arquivo.split('-')[-1][:8]}" if m.foto_arquivo else None,
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


@rotas.put("/{id}/foto", response_model=MemoriaLida)
def enviar_foto(id: str, arquivo: UploadFile, memorias: MemoriasDep, config: ConfigDep):
    """Envia (ou troca) a foto da memória. Ela é reduzida e perde os metadados (como o local GPS)."""
    memoria = obter_ou_404(memorias, id)
    # rota síncrona: o FastAPI a roda em outra thread, e reduzir a foto não trava o servidor
    conteudo = arquivo.file.read(fotos.TAMANHO_MAXIMO_ENVIO + 1)
    try:
        jpeg = fotos.preparar(conteudo)
    except fotos.FotoInvalida as erro:
        codigo = status.HTTP_413_CONTENT_TOO_LARGE if len(conteudo) > fotos.TAMANHO_MAXIMO_ENVIO else status.HTTP_422_UNPROCESSABLE_CONTENT
        raise HTTPException(codigo, str(erro)) from None
    anterior = memoria.foto_arquivo
    nome = fotos.gravar(config.pasta_fotos, memorias.usuario_id, memoria.id, jpeg)
    alterada = memorias.atualizar(memoria, {"foto_arquivo": nome})
    if anterior:
        fotos.apagar(config.pasta_fotos, memorias.usuario_id, anterior)
    return _ler([alterada], memorias.listar())[0]


@rotas.get("/{id}/foto", response_class=FileResponse)
def ler_foto(id: str, memorias: MemoriasDep, config: ConfigDep):
    """A foto da memória. Só o dono consegue ver."""
    memoria = obter_ou_404(memorias, id)
    if not memoria.foto_arquivo:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Esta memória não tem foto.")
    arquivo = fotos.caminho(config.pasta_fotos, memorias.usuario_id, memoria.foto_arquivo)
    if not arquivo.exists():
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Arquivo da foto não encontrado.")
    # "private": só o navegador de quem pediu guarda cópia, nenhum intermediário
    return FileResponse(arquivo, media_type="image/jpeg", headers={"Cache-Control": "private, max-age=31536000, immutable"})


@rotas.delete("/{id}/foto", response_model=MemoriaLida)
def remover_foto(id: str, memorias: MemoriasDep, config: ConfigDep):
    memoria = obter_ou_404(memorias, id)
    anterior = memoria.foto_arquivo
    alterada = memorias.atualizar(memoria, {"foto_arquivo": None})
    if anterior:
        fotos.apagar(config.pasta_fotos, memorias.usuario_id, anterior)
    return _ler([alterada], memorias.listar())[0]
