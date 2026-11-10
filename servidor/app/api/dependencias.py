"""Peças que as rotas recebem prontas do FastAPI (via `Depends`)."""

from __future__ import annotations

from typing import Annotated

from datetime import timedelta

from fastapi import Depends, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from sqlmodel import Session, select

from app.banco import obter_sessao
from app.config import Configuracao, obter_configuracao
from app.modelos import Capitulo, Intencao, Memoria, Sessao, Usuario, agora, em_utc
from app.repositorio import NaoEncontrado, Repositorio
from app.seguranca import hash_do_codigo

SessaoDep = Annotated[Session, Depends(obter_sessao)]
ConfigDep = Annotated[Configuracao, Depends(obter_configuracao)]


NOME_DO_COOKIE = "lj_sessao"


def sessao_atual(request: Request, sessao: SessaoDep) -> Sessao:
    """A sessão do aparelho que fez a requisição, pelo cookie. Sem sessão válida: 401."""
    codigo = request.cookies.get(NOME_DO_COOKIE)
    registro = None
    if codigo:
        registro = sessao.exec(select(Sessao).where(Sessao.codigo_hash == hash_do_codigo(codigo))).first()
    if registro is None or em_utc(registro.expira_em) <= agora():
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Entre na sua conta para continuar.")
    # registra o uso no máximo uma vez por hora, para não gravar no banco a cada clique
    if agora() - em_utc(registro.ultimo_uso) > timedelta(hours=1):
        registro.ultimo_uso = agora()
        sessao.add(registro)
        sessao.commit()
    return registro


SessaoAtualDep = Annotated[Sessao, Depends(sessao_atual)]


def usuario_atual(registro: SessaoAtualDep, sessao: SessaoDep) -> Usuario:
    usuario = sessao.get(Usuario, registro.usuario_id)
    if usuario is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Entre na sua conta para continuar.")
    return usuario


UsuarioDep = Annotated[Usuario, Depends(usuario_atual)]


def administrador(usuario: UsuarioDep) -> Usuario:
    if not usuario.administrador:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Só o administrador pode fazer isso.")
    return usuario


AdministradorDep = Annotated[Usuario, Depends(administrador)]


def _repositorio(modelo):
    def criar(sessao: SessaoDep, usuario: UsuarioDep) -> Repositorio:
        return Repositorio(sessao, usuario.id, modelo)

    return criar


MemoriasDep = Annotated[Repositorio[Memoria], Depends(_repositorio(Memoria))]
CapitulosDep = Annotated[Repositorio[Capitulo], Depends(_repositorio(Capitulo))]
IntencoesDep = Annotated[Repositorio[Intencao], Depends(_repositorio(Intencao))]


def obter_ou_404(repositorio: Repositorio, id: str):
    try:
        return repositorio.obter(id)
    except NaoEncontrado:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Registro não encontrado.") from None


def exigir_memorias(memorias: Repositorio[Memoria], ids: list[str], campo: str) -> None:
    """Recusa ligações para memórias que não existem ou são de outra pessoa."""
    faltando = set(ids) - memorias.existentes(ids)
    if faltando:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            f"'{campo}' cita memória que não existe: {', '.join(sorted(faltando))}.",
        )


def juntar_mudancas(esquema, atual, mudancas):
    """Aplica as mudanças sobre o registro atual e valida o resultado inteiro.

    Algumas regras dependem de dois campos (fim depois do início, data no
    passado), então valer cada campo sozinho não basta. Se o resultado for
    inválido, responde 422, como qualquer outro dado inválido.
    """
    juntos = {**atual.model_dump(include=set(esquema.model_fields)), **mudancas.model_dump(exclude_unset=True)}
    try:
        return esquema.model_validate(juntos)
    except ValidationError as erro:
        raise RequestValidationError(erro.errors(include_url=False)) from None
