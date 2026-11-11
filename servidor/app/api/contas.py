"""Entrar, sair, criar conta por convite, trocar e redefinir senha, aparelhos conectados."""

from datetime import timedelta

from fastapi import APIRouter, HTTPException, Request, Response, status
from sqlmodel import select

from app.api.dependencias import NOME_DO_COOKIE, ConfigDep, SessaoAtualDep, SessaoDep, UsuarioDep
from app.config import obter_configuracao
from app.esquemas import ContaLida, Entrada, NovaConta, SenhaRedefinida, SessaoLida, TrocaDeSenha
from app.modelos import Convite, Redefinicao, Sessao, Usuario, agora, em_utc
from app.seguranca import Limitador, hash_da_senha, hash_do_codigo, novo_codigo, senha_confere

rotas = APIRouter(prefix="/api", tags=["conta"])

DURACAO_DA_SESSAO = timedelta(days=90)
ERRO_DE_ENTRADA = "E-mail ou senha incorretos."

# 5 erros por e-mail e 20 por endereço a cada 15 minutos
tentativas_por_email = Limitador(5, 15 * 60)
tentativas_por_endereco = Limitador(20, 15 * 60)
# códigos de convite e redefinição: 20 tentativas por endereço a cada 15 minutos
tentativas_de_codigo = Limitador(20, 15 * 60)


def _endereco(request: Request) -> str:
    """Endereço de quem fez o pedido, para o limite de tentativas.

    Atrás do túnel da Cloudflare, todo pedido chega vindo do túnel; o endereço real
    vem num cabeçalho (LJ_CABECALHO_DO_IP). Só ligue essa opção se o servidor não for
    alcançável por outro caminho, porque qualquer um poderia inventar o cabeçalho.
    """
    cabecalho = obter_configuracao().cabecalho_do_ip
    if cabecalho and request.headers.get(cabecalho):
        return request.headers[cabecalho].strip()[:64]
    return request.client.host if request.client else "desconhecido"


def _abrir_sessao(resposta: Response, request: Request, sessao: SessaoDep, usuario: Usuario, seguro: bool) -> None:
    # aproveita para apagar as sessões vencidas de todo mundo
    for vencida in sessao.exec(select(Sessao).where(Sessao.expira_em < agora())):
        sessao.delete(vencida)
    codigo = novo_codigo()
    sessao.add(Sessao(
        codigo_hash=hash_do_codigo(codigo), usuario_id=usuario.id,
        aparelho=request.headers.get("user-agent", "")[:200],
        expira_em=agora() + DURACAO_DA_SESSAO,
    ))
    sessao.commit()
    resposta.set_cookie(
        NOME_DO_COOKIE, codigo, max_age=int(DURACAO_DA_SESSAO.total_seconds()),
        httponly=True,  # o JavaScript da página não consegue ler o cookie
        secure=seguro,  # em produção, só por HTTPS
        samesite="lax",  # outros sites não conseguem enviar o cookie em pedidos que alteram dados
        path="/",
    )


def _encerrar_sessoes(sessao: SessaoDep, usuario_id: str, exceto: str | None = None) -> None:
    for s in sessao.exec(select(Sessao).where(Sessao.usuario_id == usuario_id)):
        if s.id != exceto:
            sessao.delete(s)
    sessao.commit()


def _limitar_codigos(request: Request) -> None:
    if tentativas_de_codigo.bloqueado(_endereco(request)):
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, "Muitas tentativas. Espere alguns minutos.")
    tentativas_de_codigo.registrar(_endereco(request))


@rotas.post("/entrar", response_model=ContaLida)
def entrar(dados: Entrada, request: Request, resposta: Response, sessao: SessaoDep, config: ConfigDep):
    endereco = _endereco(request)
    if tentativas_por_email.bloqueado(dados.email) or tentativas_por_endereco.bloqueado(endereco):
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, "Muitas tentativas. Espere alguns minutos.")
    usuario = sessao.exec(select(Usuario).where(Usuario.email == dados.email)).first()
    if not senha_confere(usuario.senha_hash if usuario else None, dados.senha):
        tentativas_por_email.registrar(dados.email)
        tentativas_por_endereco.registrar(endereco)
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, ERRO_DE_ENTRADA)
    tentativas_por_email.zerar(dados.email)
    _abrir_sessao(resposta, request, sessao, usuario, not config.desenvolvimento)
    return usuario


@rotas.post("/sair", status_code=status.HTTP_204_NO_CONTENT)
def sair(atual: SessaoAtualDep, sessao: SessaoDep):
    sessao.delete(atual)
    sessao.commit()
    resposta = Response(status_code=status.HTTP_204_NO_CONTENT)
    resposta.delete_cookie(NOME_DO_COOKIE, path="/")
    return resposta


@rotas.post("/contas", response_model=ContaLida, status_code=status.HTTP_201_CREATED)
def criar_conta(dados: NovaConta, request: Request, resposta: Response, sessao: SessaoDep, config: ConfigDep):
    """Cria uma conta a partir de um convite e já entra nela."""
    _limitar_codigos(request)
    convite = sessao.exec(select(Convite).where(Convite.codigo_hash == hash_do_codigo(dados.codigo))).first()
    if (convite is None or convite.usado_por or convite.cancelado_em
            or em_utc(convite.valido_ate) <= agora()):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Este convite não vale mais. Peça um novo.")
    if sessao.exec(select(Usuario).where(Usuario.email == dados.email)).first():
        raise HTTPException(status.HTTP_409_CONFLICT, "Já existe uma conta com este e-mail.")
    usuario = Usuario(email=dados.email, senha_hash=hash_da_senha(dados.senha))
    sessao.add(usuario)
    sessao.commit()
    sessao.refresh(usuario)
    convite.usado_por = usuario.id
    sessao.add(convite)
    _abrir_sessao(resposta, request, sessao, usuario, not config.desenvolvimento)
    return usuario


@rotas.post("/redefinir-senha", status_code=status.HTTP_204_NO_CONTENT)
def redefinir_senha(dados: SenhaRedefinida, request: Request, sessao: SessaoDep):
    """Cria senha nova com o link gerado pelo administrador. Desconecta todos os aparelhos."""
    _limitar_codigos(request)
    pedido = sessao.exec(select(Redefinicao).where(Redefinicao.codigo_hash == hash_do_codigo(dados.codigo))).first()
    if pedido is None or pedido.usado_em or em_utc(pedido.valido_ate) <= agora():
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Este link não vale mais. Peça um novo ao administrador.")
    usuario = sessao.get(Usuario, pedido.usuario_id)
    usuario.senha_hash = hash_da_senha(dados.senha_nova)
    pedido.usado_em = agora()
    sessao.add(usuario)
    sessao.add(pedido)
    sessao.commit()
    _encerrar_sessoes(sessao, usuario.id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@rotas.get("/conta", response_model=ContaLida)
def ler_conta(usuario: UsuarioDep):
    return usuario


@rotas.post("/conta/senha", status_code=status.HTTP_204_NO_CONTENT)
def trocar_senha(dados: TrocaDeSenha, usuario: UsuarioDep, atual: SessaoAtualDep, sessao: SessaoDep):
    """Troca a senha. Os outros aparelhos são desconectados; este continua."""
    if tentativas_por_email.bloqueado(usuario.email):
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, "Muitas tentativas. Espere alguns minutos.")
    if not senha_confere(usuario.senha_hash, dados.senha_atual):
        tentativas_por_email.registrar(usuario.email)  # o mesmo limite do login
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "A senha atual não confere.")
    usuario.senha_hash = hash_da_senha(dados.senha_nova)
    sessao.add(usuario)
    sessao.commit()
    _encerrar_sessoes(sessao, usuario.id, exceto=atual.id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@rotas.get("/conta/sessoes", response_model=list[SessaoLida])
def listar_sessoes(usuario: UsuarioDep, atual: SessaoAtualDep, sessao: SessaoDep):
    """Aparelhos conectados a esta conta."""
    lista = sessao.exec(select(Sessao).where(Sessao.usuario_id == usuario.id).order_by(Sessao.ultimo_uso.desc()))
    return [SessaoLida(id=s.id, aparelho=s.aparelho, criado_em=s.criado_em, ultimo_uso=s.ultimo_uso, esta=s.id == atual.id)
            for s in lista if em_utc(s.expira_em) > agora()]


@rotas.delete("/conta/sessoes/{id}", status_code=status.HTTP_204_NO_CONTENT)
def desconectar(id: str, usuario: UsuarioDep, sessao: SessaoDep):
    alvo = sessao.get(Sessao, id)
    if alvo is None or alvo.usuario_id != usuario.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Aparelho não encontrado.")
    sessao.delete(alvo)
    sessao.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
