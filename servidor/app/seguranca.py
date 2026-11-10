"""Senhas, códigos secretos e limite de tentativas.

- Senhas: guardadas só como hash Argon2 (não dá para voltar à senha).
- Códigos (sessão, convite, redefinição): o aparelho ou o link guarda o código;
  o banco guarda só o SHA-256 dele. Quem ler o banco não consegue usá-los.
"""

from __future__ import annotations

import hashlib
import secrets
import threading
import time
from collections import defaultdict, deque

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError

_hasher = PasswordHasher()
# hash de uma senha qualquer, para gastar o mesmo tempo quando o e-mail não existe
_HASH_FALSO = _hasher.hash("senha-que-ninguem-tem")

SENHA_MINIMA = 10
SENHA_MAXIMA = 128


def hash_da_senha(senha: str) -> str:
    return _hasher.hash(senha)


def senha_confere(hash_guardado: str | None, senha: str) -> bool:
    """Confere a senha. Sem hash (usuário inexistente), gasta o mesmo tempo e devolve False."""
    try:
        return _hasher.verify(hash_guardado or _HASH_FALSO, senha) and hash_guardado is not None
    except (VerificationError, InvalidHashError):
        return False


def novo_codigo() -> str:
    """Código aleatório de 256 bits, seguro para pôr num cookie ou num link."""
    return secrets.token_urlsafe(32)


def hash_do_codigo(codigo: str) -> str:
    return hashlib.sha256(codigo.encode()).hexdigest()


class Limitador:
    """Conta tentativas por chave numa janela de tempo. Guarda tudo na memória do servidor.

    Serve para um servidor com um processo só (o caso do Raspberry Pi). Reiniciar o
    servidor zera as contagens.
    """

    def __init__(self, maximo: int, janela_segundos: float, relogio=time.monotonic):
        self.maximo = maximo
        self.janela = janela_segundos
        self.relogio = relogio
        self._tentativas: dict[str, deque[float]] = defaultdict(deque)
        self._trava = threading.Lock()

    def _limpar(self, chave: str, agora: float) -> deque[float]:
        fila = self._tentativas[chave]
        while fila and agora - fila[0] > self.janela:
            fila.popleft()
        return fila

    def bloqueado(self, chave: str) -> bool:
        with self._trava:
            return len(self._limpar(chave, self.relogio())) >= self.maximo

    def registrar(self, chave: str) -> None:
        with self._trava:
            agora = self.relogio()
            self._limpar(chave, agora).append(agora)

    def zerar(self, chave: str) -> None:
        with self._trava:
            self._tentativas.pop(chave, None)
