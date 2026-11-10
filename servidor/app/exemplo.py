"""Preenche a conta de desenvolvimento com uma vida FICTÍCIA, para ver a linha do tempo.

Rode, dentro da pasta `servidor`:  python -m app.exemplo
Use `--substituir` para apagar o que já existe na conta de desenvolvimento antes.
Só funciona em modo desenvolvimento.
"""

from __future__ import annotations

import sys
from datetime import date, timedelta

from sqlmodel import Session, select

from app.banco import criar_tabelas, obter_motor
from app.config import obter_configuracao
from app.modelos import Capitulo, Intencao, Memoria, Usuario, agora
from app.repositorio import Repositorio

CAPITULOS = [
    ("Infância em Olinda", "1990-03-14", "2001-01-31", "menta", True),
    ("Curitiba e a escola", "2001-02-01", "2007-12-20", "azul", True),
    ("Faculdade de Arquitetura", "2008-03-01", "2013-12-15", "ambar", True),
    ("Primeiro escritório", "2014-02-10", "2018-06-30", "laranja", True),
    ("Com o Davi", "2015-08-22", "2021-04-10", "rosa", False),
    ("O ano sem meu pai", "2017-09-19", "2018-10-30", "lavanda", False),
    ("Estúdio próprio em São Paulo", "2018-11-05", None, "coral", True),
    ("Aprendendo a correr", "2023-01-15", None, "menta", False),
]

# (chave, data, texto, emoção, intensidade, marcante, veio_de)
MEMORIAS = [
    ("natal", "1994-12-24", "Primeiro Natal de que me lembro. A casa da vó Zefa cheia, e eu dormindo debaixo da mesa.", "alegria", 2, False, None),
    ("carnaval", "1996-02-18", "Carnaval em Olinda no ombro do meu pai. Os bonecos gigantes me davam medo e eu não queria ir embora.", "alegria", 3, True, None),
    ("bicicleta", "1998-07-10", "Aprendi a andar de bicicleta na ladeira. Ralei os dois joelhos.", "orgulho", 1, False, None),
    ("mudanca", "2001-02-05", "Mudança para Curitiba. Chorei o voo inteiro e nunca tinha sentido tanto frio.", "saudade", 3, True, None),
    ("desenho", "2003-09-12", "A professora Lúcia pendurou meu desenho da Ópera de Arame no corredor da escola.", "orgulho", 2, False, None),
    ("ilha", "2005-06-25", "Primeira viagem sem meus pais: Ilha do Mel com a turma.", "alegria", 2, False, None),
    ("vestibular", "2007-12-14", "Passei no vestibular de Arquitetura. Meu pai buzinou a rua inteira.", "orgulho", 3, True, "desenho"),
    ("faculdade", "2008-03-03", "Primeiro dia de faculdade. Não entendi nada na aula de estruturas.", "incerteza", 1, False, None),
    ("lisboa", "2010-07-20", "Inverno em Lisboa. Desenhei azulejos por três semanas.", "alegria", 3, True, None),
    ("reprovei", "2012-05-08", "Reprovei em Projeto VI. Pensei em largar o curso.", "tristeza", 2, False, None),
    ("formatura", "2013-12-13", "Formatura. A banca elogiou justamente o projeto que refiz depois de reprovar.", "orgulho", 3, True, "reprovei"),
    ("emprego", "2014-02-10", "Primeiro emprego, no escritório da Renata. Salário pequeno, prancheta grande.", "incerteza", 1, False, None),
    ("davi", "2015-08-22", "Conheci o Davi num show na Pedreira.", "alegria", 2, False, None),
    ("padaria", "2016-10-02", "Primeira obra entregue: a padaria da rua Itupava.", "orgulho", 2, False, None),
    ("pai", "2017-09-19", "Meu pai morreu. Escrevo isso só para que a data fique guardada.", "tristeza", 3, True, None),
    ("olinda", "2018-03-11", "Voltei a Olinda sozinha e subi a ladeira da Misericórdia.", "saudade", 2, False, "pai"),
    ("demissao", "2018-06-29", "Pedi demissão. Não sabia o que vinha depois.", "incerteza", 2, False, "pai"),
    ("estudio", "2018-11-05", "Abri o estúdio numa sala de 20 m² na Vila Buarque.", "orgulho", 3, True, "demissao"),
    ("quarentena", "2020-03-17", "Primeira semana de quarentena. Desenhando na mesa da cozinha.", "incerteza", 2, False, None),
    ("separacao", "2021-04-10", "Davi e eu nos separamos. Foi triste e foi certo.", "tristeza", 3, False, None),
    ("biblioteca", "2022-08-27", "A biblioteca comunitária de Parelheiros foi inaugurada.", "orgulho", 3, True, "estudio"),
    ("2km", "2023-01-15", "Corri 2 km sem parar pela primeira vez.", "orgulho", 1, False, None),
    ("meia", "2024-06-02", "Primeira meia maratona, em 2h31. Chorei no quilômetro 19.", "alegria", 3, False, "2km"),
    ("bolo", "2025-12-25", "Natal com minha mãe em São Paulo. Fizemos o bolo de rolo da vó Zefa.", "calma", 2, False, None),
]


def _memorias_recentes(hoje: date) -> list[tuple]:
    """Memórias com data relativa a hoje, para 'Hoje' e 'nesta semana, em outros anos' terem conteúdo."""
    def anos_atras(n: int, dias: int = 0) -> str:
        dia = min(hoje.day, 28) if hoje.month == 2 else hoje.day  # evita 29 de fevereiro
        return (hoje.replace(year=hoje.year - n, day=dia) + timedelta(days=dias)).isoformat()

    return [
        ("varanda", anos_atras(5, 1), "Tarde inteira na varanda lendo, sem olhar o celular.", "calma", 1, False, None),
        ("maquete", anos_atras(11, -2), "Entreguei a maquete de um projeto às três da manhã.", "orgulho", 1, False, None),
        ("ceramica", (hoje - timedelta(days=110)).isoformat(), "Comecei a aula de cerâmica aos sábados.", "calma", 1, False, None),
        ("bia", (hoje - timedelta(days=10)).isoformat(), "Almoço longo com a Bia, que eu não via há dois anos.", "alegria", 2, False, None),
    ]


def _intencoes(hoje: date) -> list[tuple]:
    def meses(n: int) -> str:
        mes = hoje.month - 1 + n
        return date(hoje.year + mes // 12, mes % 12 + 1, 1).isoformat()

    return [
        ("Viagem ao Japão na primavera", {"tipo": "data", "data": meses(5)}, "ativa"),
        ("Correr uma maratona inteira", {"tipo": "intervalo", "de": meses(12), "ate": meses(24)}, "ativa"),
        ("Projetar uma escola pública", {"tipo": "intervalo", "de": meses(36), "ate": meses(60)}, "ativa"),
        ("Morar um ano perto do mar", {"tipo": "intervalo", "de": meses(72), "ate": meses(120)}, "pausada"),
        ("Aprender violoncelo", {"tipo": "algum_dia"}, "ativa"),
        ("Levar minha mãe a Lisboa", {"tipo": "algum_dia"}, "ativa"),
        ("Escrever sobre o meu pai", {"tipo": "algum_dia"}, "ativa"),
    ]


def preencher(sessao: Session, usuario: Usuario, hoje: date) -> dict[str, int]:
    """Cria a vida de exemplo para o usuário. Devolve quantos registros criou."""
    usuario.nascimento = date(1990, 3, 14)
    usuario.sexo = "feminino"
    sessao.add(usuario)
    sessao.commit()

    capitulos = Repositorio(sessao, usuario.id, Capitulo)
    for nome, inicio, fim, cor, principal in CAPITULOS:
        capitulos.criar({"nome": nome, "inicio": date.fromisoformat(inicio),
                         "fim": date.fromisoformat(fim) if fim else None, "cor": cor, "principal": principal})

    memorias = Repositorio(sessao, usuario.id, Memoria)
    ids: dict[str, str] = {}
    for chave, data, texto, emocao, intensidade, marcante, origem in MEMORIAS + _memorias_recentes(hoje):
        criada = memorias.criar({
            "data": date.fromisoformat(data), "texto": texto, "emocao": emocao, "intensidade": intensidade,
            "marcante": marcante, "veio_de": [ids[origem]] if origem else [],
        })
        ids[chave] = criada.id

    intencoes = Repositorio(sessao, usuario.id, Intencao)
    lista = _intencoes(hoje)
    for nome, horizonte, situacao in lista:
        intencoes.criar({"nome": nome, "horizonte": horizonte, "status": situacao})

    return {"capitulos": len(CAPITULOS), "memorias": len(ids), "intencoes": len(lista)}


def apagar_conteudo(sessao: Session, usuario: Usuario) -> None:
    for modelo in (Intencao, Memoria, Capitulo):
        repositorio = Repositorio(sessao, usuario.id, modelo)
        for registro in repositorio.listar():
            registro.excluido_em = agora()
            sessao.add(registro)
    sessao.commit()


def main(argumentos: list[str]) -> int:
    config = obter_configuracao()
    if not config.desenvolvimento:
        print("Os dados de exemplo só podem ser criados em modo desenvolvimento.")
        return 1
    motor = obter_motor()
    criar_tabelas(motor)
    with Session(motor) as sessao:
        usuario = sessao.exec(select(Usuario).where(Usuario.email == config.email_desenvolvimento)).first()
        if usuario is None:
            usuario = Usuario(email=config.email_desenvolvimento)
            sessao.add(usuario)
            sessao.commit()
            sessao.refresh(usuario)
        if Repositorio(sessao, usuario.id, Memoria).listar():
            if "--substituir" not in argumentos:
                print(f"A conta {usuario.email} já tem memórias. Use --substituir para apagá-las e recriar.")
                return 1
            apagar_conteudo(sessao, usuario)
        criados = preencher(sessao, usuario, date.today())
        email = usuario.email
    print(f"Vida de exemplo criada para {email}: "
          f"{criados['memorias']} memórias, {criados['capitulos']} capítulos, {criados['intencoes']} intenções.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
