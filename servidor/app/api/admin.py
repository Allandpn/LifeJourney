"""Rotas do administrador: convites e links de redefinição de senha.

O administrador não vê memórias, capítulos, intenções nem perfil de ninguém por aqui.
"""

from datetime import timedelta

from fastapi import APIRouter, HTTPException, Response, status
from sqlmodel import select

from app.api.dependencias import AdministradorDep, SessaoDep
from app.esquemas import ConviteLido, LinkGerado, PedidoDeRedefinicao
from app.modelos import Convite, Redefinicao, Usuario, agora
from app.seguranca import hash_do_codigo, novo_codigo

rotas = APIRouter(prefix="/api/admin", tags=["administração"])

VALIDADE_DO_CONVITE = timedelta(days=7)
VALIDADE_DA_REDEFINICAO = timedelta(days=1)


@rotas.post("/convites", response_model=LinkGerado, status_code=status.HTTP_201_CREATED)
def criar_convite(admin: AdministradorDep, sessao: SessaoDep):
    """Gera um link de convite. Ele aparece só agora: copie e envie para a pessoa."""
    codigo = novo_codigo()
    convite = Convite(codigo_hash=hash_do_codigo(codigo), criado_por=admin.id, valido_ate=agora() + VALIDADE_DO_CONVITE)
    sessao.add(convite)
    sessao.commit()
    return LinkGerado(caminho=f"/#convite-{codigo}", valido_ate=convite.valido_ate)


@rotas.get("/convites", response_model=list[ConviteLido])
def listar_convites(admin: AdministradorDep, sessao: SessaoDep):
    lista = sessao.exec(select(Convite).where(Convite.criado_por == admin.id).order_by(Convite.criado_em.desc()))
    return [ConviteLido(id=c.id, criado_em=c.criado_em, valido_ate=c.valido_ate, usado=c.usado_por is not None,
                        cancelado=c.cancelado_em is not None) for c in lista]


@rotas.delete("/convites/{id}", status_code=status.HTTP_204_NO_CONTENT)
def cancelar_convite(id: str, admin: AdministradorDep, sessao: SessaoDep):
    convite = sessao.get(Convite, id)
    if convite is None or convite.criado_por != admin.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Convite não encontrado.")
    convite.cancelado_em = agora()
    sessao.add(convite)
    sessao.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@rotas.post("/redefinicoes", response_model=LinkGerado, status_code=status.HTTP_201_CREATED)
def criar_redefinicao(dados: PedidoDeRedefinicao, admin: AdministradorDep, sessao: SessaoDep):
    """Gera um link para a pessoa criar senha nova. Vale um dia e uma vez."""
    usuario = sessao.exec(select(Usuario).where(Usuario.email == dados.email)).first()
    if usuario is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Não há conta com este e-mail.")
    codigo = novo_codigo()
    pedido = Redefinicao(codigo_hash=hash_do_codigo(codigo), usuario_id=usuario.id,
                         valido_ate=agora() + VALIDADE_DA_REDEFINICAO)
    sessao.add(pedido)
    sessao.commit()
    return LinkGerado(caminho=f"/#redefinir-{codigo}", valido_ate=pedido.valido_ate)
