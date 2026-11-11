"""Servidor do Vida em Semanas."""

import os

__version__ = "0.1.0"

# Arquivos criados pelo servidor e pelos comandos (banco, fotos, cópias) ficam legíveis
# só pelo dono, e não por outros usuários do Raspberry Pi.
os.umask(0o077)
