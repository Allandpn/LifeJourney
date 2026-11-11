"""Comandos de administração das contas, para rodar no servidor.

Dentro da pasta `servidor`:
    python -m app.contas criar-admin voce@exemplo.com     cria a conta do administrador
    python -m app.contas redefinir-senha voce@exemplo.com troca a senha de uma conta

A senha é pedida no terminal e não aparece na tela. Sem terminal (num script), acrescente
--link: em vez de pedir a senha, o comando imprime um link de uso único, válido por um dia,
para a pessoa criar a senha no aplicativo.
"""

from __future__ import annotations

import getpass
import sys

from sqlmodel import Session, select

from app.banco import obter_motor, preparar_banco
from datetime import timedelta

from app.config import obter_configuracao
from app.modelos import Redefinicao, Sessao, Usuario, agora
from app.seguranca import SENHA_MINIMA, hash_da_senha, hash_do_codigo, novo_codigo


def _pedir_senha() -> str:
    senha = getpass.getpass(f"Senha (mínimo {SENHA_MINIMA} caracteres): ")
    if len(senha) < SENHA_MINIMA:
        raise SystemExit(f"A senha precisa de pelo menos {SENHA_MINIMA} caracteres.")
    if getpass.getpass("Repita a senha: ") != senha:
        raise SystemExit("As senhas não conferem.")
    return senha


def link_de_senha(sessao: Session, usuario: Usuario) -> str:
    """Cria um link de uso único (um dia) para a pessoa criar a senha no aplicativo."""
    codigo = novo_codigo()
    sessao.add(Redefinicao(codigo_hash=hash_do_codigo(codigo), usuario_id=usuario.id, valido_ate=agora() + timedelta(days=1)))
    sessao.commit()
    origens = obter_configuracao().origens_permitidas
    return f"https://{origens[0]}/#redefinir-{codigo}" if origens else f"/#redefinir-{codigo}"


def main(argumentos: list[str]) -> int:
    com_link = "--link" in argumentos
    argumentos = [a for a in argumentos if a != "--link"]
    if len(argumentos) != 2 or argumentos[0] not in ("criar-admin", "redefinir-senha"):
        print(__doc__)
        return 1
    comando, email = argumentos[0], argumentos[1].strip().lower()
    if "@" not in email:
        print("E-mail inválido.")
        return 1
    motor = obter_motor()
    preparar_banco(motor)
    with Session(motor) as sessao:
        usuario = sessao.exec(select(Usuario).where(Usuario.email == email)).first()
        if comando == "criar-admin":
            if usuario and usuario.senha_hash:
                print(f"Já existe uma conta com {email}. Use redefinir-senha para trocar a senha.")
                return 1
            usuario = usuario or Usuario(email=email)
            usuario.senha_hash = None if com_link else hash_da_senha(_pedir_senha())
            usuario.administrador = True
            sessao.add(usuario)
            sessao.commit()
            if com_link:
                print(f"Administrador {email} criado. Abra este link (vale um dia, uma vez) para criar a senha:")
                print(link_de_senha(sessao, usuario))
            else:
                print(f"Administrador {email} pronto. Entre no aplicativo com este e-mail.")
        else:
            if usuario is None:
                print(f"Não há conta com {email}.")
                return 1
            for s in sessao.exec(select(Sessao).where(Sessao.usuario_id == usuario.id)):
                sessao.delete(s)
            if com_link:
                usuario.senha_hash = None
                sessao.add(usuario)
                sessao.commit()
                print(f"Senha de {email} apagada e aparelhos desconectados. Link para criar a nova (vale um dia, uma vez):")
                print(link_de_senha(sessao, usuario))
            else:
                usuario.senha_hash = hash_da_senha(_pedir_senha())
                sessao.add(usuario)
                sessao.commit()
                print(f"Senha de {email} trocada. Todos os aparelhos foram desconectados.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
