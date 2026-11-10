"""Peças que as rotas recebem prontas do FastAPI (via `Depends`)."""

from __future__ import annotations

import logging
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from sqlmodel import Session, select

from app.banco import obter_sessao
from app.config import Configuracao, obter_configuracao
from app.modelos import Capitulo, Intencao, Memoria, Usuario
from app.repositorio import NaoEncontrado, Repositorio

log = logging.getLogger(__name__)

SessaoDep = Annotated[Session, Depends(obter_sessao)]
ConfigDep = Annotated[Configuracao, Depends(obter_configuracao)]


def usuario_atual(sessao: SessaoDep, config: ConfigDep) -> Usuario:
    """Quem está fazendo a requisição.

    Até a etapa 5 (login) não há senha: em modo desenvolvimento, toda requisição
    é do usuário de desenvolvimento, criado na primeira vez. Em produção, tudo é
    recusado, para o servidor nunca ir ao ar sem login por engano.
    """
    if not config.desenvolvimento:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "O login ainda não foi implementado.")
    usuario = sessao.exec(select(Usuario).where(Usuario.email == config.email_desenvolvimento)).first()
    if usuario is None:
        usuario = Usuario(email=config.email_desenvolvimento)
        sessao.add(usuario)
        sessao.commit()
        sessao.refresh(usuario)
        log.warning("Usuário de desenvolvimento criado: %s", usuario.email)
    return usuario


UsuarioDep = Annotated[Usuario, Depends(usuario_atual)]


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
