"""Acesso aos dados de UM usuário.

Este é o ponto único onde o isolamento entre contas acontece: toda consulta
passa por `_consulta`, que filtra pelo dono e esconde o que foi excluído.
As rotas da API nunca consultam o banco por conta própria.
"""

from __future__ import annotations

from typing import Any, Generic, TypeVar

from sqlmodel import Session, select

from app.modelos import Registro, agora

T = TypeVar("T", bound=Registro)


class NaoEncontrado(Exception):
    """O registro não existe, foi excluído ou é de outra pessoa (a resposta é a mesma)."""


class Repositorio(Generic[T]):
    def __init__(self, sessao: Session, usuario_id: str, modelo: type[T]):
        self.sessao = sessao
        self.usuario_id = usuario_id
        self.modelo = modelo

    def _consulta(self):
        return select(self.modelo).where(
            self.modelo.usuario_id == self.usuario_id,
            self.modelo.excluido_em.is_(None),  # type: ignore[union-attr]
        )

    def listar(self, *condicoes: Any, ordem: Any = None) -> list[T]:
        consulta = self._consulta().where(*condicoes)
        if ordem is not None:
            consulta = consulta.order_by(ordem)
        return list(self.sessao.exec(consulta))

    def obter(self, id: str) -> T:
        registro = self.sessao.exec(self._consulta().where(self.modelo.id == id)).first()
        if registro is None:
            raise NaoEncontrado(id)
        return registro

    def existentes(self, ids: list[str]) -> set[str]:
        """Quais destes ids existem e pertencem a este usuário."""
        if not ids:
            return set()
        consulta = self._consulta().where(self.modelo.id.in_(ids))  # type: ignore[attr-defined]
        return {registro.id for registro in self.sessao.exec(consulta)}

    def criar(self, dados: dict[str, Any]) -> T:
        registro = self.modelo(**dados, usuario_id=self.usuario_id)
        self.sessao.add(registro)
        self.sessao.commit()
        self.sessao.refresh(registro)
        return registro

    def atualizar(self, registro: T, dados: dict[str, Any]) -> T:
        for campo, valor in dados.items():
            setattr(registro, campo, valor)
        registro.atualizado_em = agora()
        self.sessao.add(registro)
        self.sessao.commit()
        self.sessao.refresh(registro)
        return registro

    def apagar_de_vez(self, registros: list[T]) -> None:
        """Remove do banco de verdade (para dados sensíveis). Só aceita registros deste usuário."""
        for registro in registros:
            if registro.usuario_id != self.usuario_id:
                raise NaoEncontrado(registro.id)
            self.sessao.delete(registro)
        self.sessao.commit()

    def excluir(self, registro: T) -> None:
        registro.excluido_em = agora()
        registro.atualizado_em = registro.excluido_em
        self.sessao.add(registro)
        self.sessao.commit()
