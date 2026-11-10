from datetime import date

from sqlalchemy.pool import StaticPool
from sqlmodel import Session

from app.banco import criar_motor, criar_tabelas
from app.esquemas import CapituloDados, IntencaoDados, MemoriaDados
from app.exemplo import preencher
from app.modelos import Capitulo, Intencao, Memoria, Usuario
from app.repositorio import Repositorio


def test_vida_de_exemplo_passa_nas_validacoes_da_api():
    motor = criar_motor("sqlite://", poolclass=StaticPool)
    criar_tabelas(motor)
    with Session(motor) as sessao:
        usuario = Usuario(email="exemplo@exemplo.local")
        sessao.add(usuario)
        sessao.commit()
        preencher(sessao, usuario, date(2026, 11, 10))

        for modelo, esquema in ((Memoria, MemoriaDados), (Capitulo, CapituloDados), (Intencao, IntencaoDados)):
            registros = Repositorio(sessao, usuario.id, modelo).listar()
            assert registros
            for r in registros:
                esquema.model_validate(r.model_dump(include=set(esquema.model_fields)))
