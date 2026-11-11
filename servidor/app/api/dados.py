"""Exportar e importar os dados da própria conta, e apagar a conta."""

import shutil
from datetime import date

from fastapi import APIRouter, HTTPException, Request, Response, UploadFile, status
from pydantic import BaseModel, ConfigDict
from sqlmodel import select

from app import exportacao, fotos
from app.api.contas import tentativas_por_email
from app.api.dependencias import NOME_DO_COOKIE, ConfigDep, SessaoDep, UsuarioDep
from app.modelos import Capitulo, Convite, Intencao, Memoria, Redefinicao, RespostasDeSaude, Sessao, agora
from app.seguranca import senha_confere

rotas = APIRouter(prefix="/api", tags=["seus dados"])


@rotas.get("/exportacao", response_class=Response)
def exportar(usuario: UsuarioDep, sessao: SessaoDep, config: ConfigDep):
    """Um ZIP com tudo da conta: dados.json, as fotos e memorias.md. Marca a data do último backup."""
    conteudo = exportacao.exportar(sessao, usuario, config.pasta_fotos)
    usuario.ultimo_backup = agora()
    sessao.add(usuario)
    sessao.commit()
    nome = f"vida-em-semanas-{date.today().isoformat()}.zip"
    return Response(conteudo, media_type="application/zip",
                    headers={"Content-Disposition": f'attachment; filename="{nome}"', "Cache-Control": "no-store"})


@rotas.post("/importacao")
def importar(arquivo: UploadFile, usuario: UsuarioDep, sessao: SessaoDep, config: ConfigDep):
    """Traz os dados de um ZIP exportado. Registros iguais não se duplicam; os mais recentes ganham."""
    conteudo = arquivo.file.read(exportacao.TAMANHO_MAXIMO_DO_ZIP + 1)
    try:
        return exportacao.importar(sessao, usuario, config.pasta_fotos, conteudo)
    except exportacao.ArquivoInvalido as erro:
        codigo = status.HTTP_413_CONTENT_TOO_LARGE if len(conteudo) > exportacao.TAMANHO_MAXIMO_DO_ZIP else status.HTTP_422_UNPROCESSABLE_CONTENT
        raise HTTPException(codigo, str(erro)) from None


class ConfirmacaoDeSenha(BaseModel):
    model_config = ConfigDict(extra="forbid")
    senha: str


@rotas.post("/conta/apagar", status_code=status.HTTP_204_NO_CONTENT)
def apagar_conta(dados: ConfirmacaoDeSenha, request: Request, usuario: UsuarioDep, sessao: SessaoDep, config: ConfigDep):
    """Apaga a conta e tudo dela, de verdade: memórias, fotos, capítulos, intenções, respostas de saúde e sessões.

    Pede a senha de novo. As cópias de segurança do servidor guardam os dados até
    serem substituídas pelas mais novas (30 noites, no padrão).
    """
    if tentativas_por_email.bloqueado(usuario.email):
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, "Muitas tentativas. Espere alguns minutos.")
    if not senha_confere(usuario.senha_hash, dados.senha):
        tentativas_por_email.registrar(usuario.email)
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "A senha não confere.")

    uid = usuario.id
    for modelo in (Intencao, Memoria, Capitulo, RespostasDeSaude, Sessao, Redefinicao):
        for registro in sessao.exec(select(modelo).where(modelo.usuario_id == uid)):
            sessao.delete(registro)
    for convite in sessao.exec(select(Convite).where(Convite.criado_por == uid)):
        sessao.delete(convite)
    for convite in sessao.exec(select(Convite).where(Convite.usado_por == uid)):
        convite.usado_por = None
        convite.cancelado_em = convite.cancelado_em or agora()  # o convite continua sem valer
        sessao.add(convite)
    sessao.flush()
    sessao.delete(usuario)
    sessao.commit()
    shutil.rmtree(fotos.pasta_do_usuario(config.pasta_fotos, uid), ignore_errors=True)

    resposta = Response(status_code=status.HTTP_204_NO_CONTENT)
    resposta.delete_cookie(NOME_DO_COOKIE, path="/")
    return resposta
