"""Cópia de segurança cifrada do banco e das fotos.

    python -m app.copia fazer
    python -m app.copia restaurar ARQUIVO.age --identidade CHAVE.txt --para PASTA

`fazer` junta o banco (copiado de forma consistente, mesmo com o servidor ligado) e as
fotos num .tar.gz e cifra com o `age`, usando a CHAVE PÚBLICA de LJ_COPIA_CHAVE_PUBLICA.
O Pi consegue criar cópias, mas não abri-las: a chave privada fica guardada fora dele.
Nada sai sem cifra para a pasta de cópias. Mantém as LJ_COPIA_MANTER mais recentes (padrão 30).

`restaurar` decifra com a chave privada e extrai numa pasta nova, sem mexer nos dados em uso.
"""

from __future__ import annotations

import argparse
import os
import shutil
import sqlite3
import subprocess
import sys
import tarfile
import tempfile
from datetime import datetime
from pathlib import Path

from app.config import RAIZ_DO_REPOSITORIO, obter_configuracao

PREFIXO = "vida-em-semanas-"
SUFIXO = ".tar.gz.age"


class ErroDeCopia(RuntimeError):
    pass


def _age() -> str:
    caminho = shutil.which("age")
    if not caminho:
        raise ErroDeCopia("O programa 'age' não está instalado.")
    return caminho


def fazer(banco: Path, fotos: Path, destino: Path, chave_publica: str, manter: int = 30) -> Path:
    if not chave_publica.startswith("age1"):
        raise ErroDeCopia("Defina LJ_COPIA_CHAVE_PUBLICA com a chave pública do age (começa com age1).")
    if not banco.exists():
        raise ErroDeCopia(f"Banco não encontrado: {banco}")
    destino.mkdir(parents=True, exist_ok=True)
    nome = f"{PREFIXO}{datetime.now():%Y%m%d-%H%M%S}{SUFIXO}"

    with tempfile.TemporaryDirectory() as temporaria:
        tmp = Path(temporaria)
        # cópia consistente do SQLite, mesmo com gravações acontecendo
        origem = sqlite3.connect(banco)
        copia = sqlite3.connect(tmp / "lifejourney.db")
        with copia:
            origem.backup(copia)
        origem.close()
        copia.close()

        pacote = tmp / "pacote.tar.gz"
        with tarfile.open(pacote, "w:gz") as tar:
            tar.add(tmp / "lifejourney.db", arcname="lifejourney.db")
            if fotos.exists():
                tar.add(fotos, arcname="fotos")

        final = destino / nome
        parcial = destino / (nome + ".parcial")
        subprocess.run([_age(), "--encrypt", "--recipient", chave_publica, "--output", str(parcial), str(pacote)],
                       check=True, capture_output=True)
        parcial.rename(final)  # só aparece com o nome final quando está completa

    antigas = sorted(destino.glob(f"{PREFIXO}*{SUFIXO}"))[:-manter] if manter > 0 else []
    for velha in antigas:
        velha.unlink()
    return final


def restaurar(arquivo: Path, identidade: Path, para: Path) -> Path:
    if para.exists() and any(para.iterdir()):
        raise ErroDeCopia(f"A pasta {para} não está vazia. Escolha uma pasta nova.")
    para.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as temporaria:
        pacote = Path(temporaria) / "pacote.tar.gz"
        resultado = subprocess.run([_age(), "--decrypt", "--identity", str(identidade), "--output", str(pacote), str(arquivo)],
                                   capture_output=True, text=True)
        if resultado.returncode != 0:
            raise ErroDeCopia(f"Não foi possível decifrar: {resultado.stderr.strip()}")
        with tarfile.open(pacote, "r:gz") as tar:
            tar.extractall(para, filter="data")  # recusa caminhos perigosos dentro do pacote
    return para


def main(argumentos: list[str]) -> int:
    leitor = argparse.ArgumentParser(prog="python -m app.copia", description="Cópia de segurança cifrada.")
    comandos = leitor.add_subparsers(dest="comando", required=True)
    comandos.add_parser("fazer", help="cria uma cópia cifrada")
    r = comandos.add_parser("restaurar", help="decifra e extrai uma cópia numa pasta nova")
    r.add_argument("arquivo", type=Path)
    r.add_argument("--identidade", type=Path, required=True, help="arquivo da chave privada do age")
    r.add_argument("--para", type=Path, required=True, help="pasta nova onde extrair")
    args = leitor.parse_args(argumentos)

    config = obter_configuracao()
    try:
        if args.comando == "fazer":
            destino = Path(os.environ.get("LJ_COPIAS", RAIZ_DO_REPOSITORIO / "dados-pessoais" / "copias"))
            final = fazer(config.caminho_banco, config.pasta_fotos, destino,
                          os.environ.get("LJ_COPIA_CHAVE_PUBLICA", ""), int(os.environ.get("LJ_COPIA_MANTER", "30")))
            print(f"Cópia criada: {final} ({final.stat().st_size // 1024} KB)")
        else:
            pasta = restaurar(args.arquivo, args.identidade, args.para)
            print(f"Cópia extraída em {pasta}. Confira e só então troque os dados em uso (veja docs/09-publicacao.md).")
    except (ErroDeCopia, subprocess.CalledProcessError) as erro:
        print(f"Erro: {erro}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
