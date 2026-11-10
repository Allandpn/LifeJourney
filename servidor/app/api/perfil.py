from fastapi import APIRouter

from app.api.dependencias import SessaoDep, UsuarioDep
from app.esquemas import PerfilDados, PerfilLido

rotas = APIRouter(prefix="/api/perfil", tags=["perfil"])


@rotas.get("", response_model=PerfilLido)
def ler_perfil(usuario: UsuarioDep):
    """Data de nascimento e sexo de quem está logado."""
    return usuario


@rotas.put("", response_model=PerfilLido)
def salvar_perfil(dados: PerfilDados, usuario: UsuarioDep, sessao: SessaoDep):
    """Grava a data de nascimento e o sexo (usados na linha do tempo e no cálculo)."""
    usuario.nascimento = dados.nascimento
    usuario.sexo = dados.sexo
    sessao.add(usuario)
    sessao.commit()
    sessao.refresh(usuario)
    return usuario
