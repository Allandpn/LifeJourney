"""Fotos das memórias: redução, limpeza de metadados e armazenamento.

Cada foto é regravada como JPEG de até 1600 px no lado maior. Ao regravar,
todos os metadados (EXIF) são descartados: eles podem conter o local GPS onde
a foto foi tirada, o modelo do celular e a data exata.

Os arquivos ficam em `<pasta de fotos>/<id do usuário>/`, uma pasta por dono.
"""

from __future__ import annotations

import io
import re
import secrets
from pathlib import Path

from PIL import Image, ImageOps, UnidentifiedImageError

LADO_MAXIMO = 1600
QUALIDADE = 85
TAMANHO_MAXIMO_ENVIO = 15 * 1024 * 1024  # 15 MB
PIXELS_MAXIMOS = 60_000_000  # recusa imagens gigantes, que poderiam travar o servidor
NOME_VALIDO = re.compile(r"[0-9a-f]+-[0-9a-f]{8}\.jpg")  # só nomes criados por gravar()


class FotoInvalida(ValueError):
    pass


def preparar(conteudo: bytes) -> bytes:
    """Lê a imagem enviada e devolve um JPEG reduzido e sem metadados."""
    if len(conteudo) > TAMANHO_MAXIMO_ENVIO:
        raise FotoInvalida("A foto passa de 15 MB.")
    Image.MAX_IMAGE_PIXELS = PIXELS_MAXIMOS
    try:
        with Image.open(io.BytesIO(conteudo)) as imagem:
            imagem = ImageOps.exif_transpose(imagem)  # aplica a rotação do celular antes de descartar o EXIF
            imagem = imagem.convert("RGB")
            imagem.thumbnail((LADO_MAXIMO, LADO_MAXIMO))
            saida = io.BytesIO()
            imagem.save(saida, "JPEG", quality=QUALIDADE, optimize=True)  # sem exif=: nada de metadados
            return saida.getvalue()
    except (UnidentifiedImageError, Image.DecompressionBombError, OSError) as erro:
        raise FotoInvalida("O arquivo não é uma imagem que dê para abrir.") from erro


def pasta_do_usuario(raiz: Path, usuario_id: str) -> Path:
    if not usuario_id.isalnum():
        raise ValueError("Id de usuário inesperado.")
    return raiz / usuario_id


def gravar(raiz: Path, usuario_id: str, memoria_id: str, jpeg: bytes) -> str:
    """Grava o arquivo e devolve o nome dele. O nome muda a cada envio."""
    pasta = pasta_do_usuario(raiz, usuario_id)
    pasta.mkdir(parents=True, exist_ok=True)
    nome = f"{memoria_id}-{secrets.token_hex(4)}.jpg"
    (pasta / nome).write_bytes(jpeg)
    return nome


def caminho(raiz: Path, usuario_id: str, nome: str) -> Path:
    if not NOME_VALIDO.fullmatch(nome):
        raise ValueError("Nome de arquivo inesperado.")
    return pasta_do_usuario(raiz, usuario_id) / nome


def apagar(raiz: Path, usuario_id: str, nome: str) -> None:
    caminho(raiz, usuario_id, nome).unlink(missing_ok=True)
