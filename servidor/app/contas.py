"""Comandos de administração das contas, para rodar no servidor.

Dentro da pasta `servidor`:
    python -m app.contas criar-admin voce@exemplo.com     cria a conta do administrador
    python -m app.contas redefinir-senha voce@exemplo.com troca a senha de uma conta

A senha é pedida no terminal e não aparece na tela.
"""

from __future__ import annotations

import getpass
import sys

from sqlmodel import Session, select

from app.banco import criar_tabelas, obter_motor
from app.modelos import Sessao, Usuario
from app.seguranca import SENHA_MINIMA, hash_da_senha


def _pedir_senha() -> str:
    senha = getpass.getpass(f"Senha (mínimo {SENHA_MINIMA} caracteres): ")
    if len(senha) < SENHA_MINIMA:
        raise SystemExit(f"A senha precisa de pelo menos {SENHA_MINIMA} caracteres.")
    if getpass.getpass("Repita a senha: ") != senha:
        raise SystemExit("As senhas não conferem.")
    return senha


def main(argumentos: list[str]) -> int:
    if len(argumentos) != 2 or argumentos[0] not in ("criar-admin", "redefinir-senha"):
        print(__doc__)
        return 1
    comando, email = argumentos[0], argumentos[1].strip().lower()
    if "@" not in email:
        print("E-mail inválido.")
        return 1
    motor = obter_motor()
    criar_tabelas(motor)
    with Session(motor) as sessao:
        usuario = sessao.exec(select(Usuario).where(Usuario.email == email)).first()
        if comando == "criar-admin":
            if usuario and usuario.senha_hash:
                print(f"Já existe uma conta com {email}. Use redefinir-senha para trocar a senha.")
                return 1
            usuario = usuario or Usuario(email=email)
            usuario.senha_hash = hash_da_senha(_pedir_senha())
            usuario.administrador = True
            sessao.add(usuario)
            sessao.commit()
            print(f"Administrador {email} pronto. Entre no aplicativo com este e-mail.")
        else:
            if usuario is None:
                print(f"Não há conta com {email}.")
                return 1
            usuario.senha_hash = hash_da_senha(_pedir_senha())
            sessao.add(usuario)
            for s in sessao.exec(select(Sessao).where(Sessao.usuario_id == usuario.id)):
                sessao.delete(s)
            sessao.commit()
            print(f"Senha de {email} trocada. Todos os aparelhos foram desconectados.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
