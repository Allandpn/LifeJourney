"""Exportar e importar todos os dados de uma conta, num ZIP de formato aberto.

Conteúdo do ZIP:
- dados.json      todas as entidades, com um número de versão do formato
- fotos/<id>.jpg  a foto de cada memória, pelo id da memória
- memorias.md     as memórias em texto legível, por capítulo (para ler sem o aplicativo)

A importação casa os registros pelo id: um registro que já existe na conta só é
atualizado se o do arquivo for mais recente. Nada é duplicado. Um id que pertence a
outra conta nunca é tocado: o registro importado ganha um id novo.
"""

from __future__ import annotations

import io
import json
import re
import zipfile
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

from pydantic import ValidationError
from sqlmodel import Session, select

from app import fotos
from app.esquemas import CapituloDados, IntencaoDados, MemoriaDados
from app.modelos import Capitulo, Intencao, Memoria, Registro, RespostasDeSaude, Usuario, agora, em_utc, novo_id

FORMATO = 1
TAMANHO_MAXIMO_DO_ZIP = 500 * 1024 * 1024  # 500 MB enviados
TAMANHO_MAXIMO_DESCOMPACTADO = 1024 * 1024 * 1024  # 1 GB depois de abrir (barra "bombas" de compressão)
ID_VALIDO = re.compile(r"[0-9a-f]{32}")  # o formato que o servidor gera (uuid4 em hexadecimal)
CHAVES_DO_RESULTADO = ("idade", "hr_total", "expectativa_media", "p10", "mediana", "p90")
MESES = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"]


class ArquivoInvalido(ValueError):
    pass


# ---------- exportar ----------

def _registro(r: Registro, campos: set[str]) -> dict[str, Any]:
    dados = r.model_dump(mode="json", include=campos | {"id", "criado_em", "atualizado_em"})
    return dados


def _ativos(sessao: Session, modelo, usuario_id: str) -> list:
    consulta = select(modelo).where(modelo.usuario_id == usuario_id)
    if hasattr(modelo, "excluido_em"):
        consulta = consulta.where(modelo.excluido_em.is_(None))
    return list(sessao.exec(consulta))


def _data_legivel(d: date) -> str:
    return f"{d.day} {MESES[d.month - 1]} {d.year}"


def memorias_em_texto(usuario: Usuario, memorias: list[Memoria], capitulos: list[Capitulo]) -> str:
    """As memórias em Markdown, em ordem de data, com um título a cada capítulo principal."""
    principais = sorted([c for c in capitulos if c.principal], key=lambda c: c.inicio)

    def capitulo_de(d: date) -> Capitulo | None:
        ativos = [c for c in principais if c.inicio <= d and (c.fim is None or d <= c.fim)]
        return ativos[0] if ativos else None

    linhas = ["# Vida em Semanas", "", f"Exportado em {_data_legivel(date.today())} · {usuario.email}", ""]
    atual: object = object()
    for m in sorted(memorias, key=lambda x: x.data):
        c = capitulo_de(m.data)
        if c is not atual:
            atual = c
            if c is None:
                linhas += ["", "## Fora de capítulos", ""]
            else:
                fim = c.fim.year if c.fim else "hoje"
                linhas += ["", f"## {c.nome} ({c.inicio.year}–{fim})", ""]
        extras = ", ".join(x for x in [m.emocao, "marcante" if m.marcante else None, "com foto" if m.foto_arquivo else None] if x)
        linhas.append(f"- **{_data_legivel(m.data)}** — {m.texto}" + (f" _({extras})_" if extras else ""))
    return "\n".join(linhas).strip() + "\n"


def exportar(sessao: Session, usuario: Usuario, pasta_fotos: Path) -> bytes:
    memorias = _ativos(sessao, Memoria, usuario.id)
    capitulos = _ativos(sessao, Capitulo, usuario.id)
    intencoes = _ativos(sessao, Intencao, usuario.id)
    respostas = _ativos(sessao, RespostasDeSaude, usuario.id)

    dados = {
        "formato": FORMATO,
        "aplicativo": "Vida em Semanas",
        "exportado_em": agora().isoformat(),
        "perfil": {"nascimento": usuario.nascimento.isoformat() if usuario.nascimento else None, "sexo": usuario.sexo},
        "memorias": [{**_registro(m, set(MemoriaDados.model_fields)), "tem_foto": bool(m.foto_arquivo)} for m in memorias],
        "capitulos": [_registro(c, set(CapituloDados.model_fields)) for c in capitulos],
        "intencoes": [_registro(i, set(IntencaoDados.model_fields)) for i in intencoes],
        "respostas_de_saude": [_registro(r, {"respostas", "altura_m", "peso_kg", "versao_config", "resultado"}) for r in respostas],
    }

    saida = io.BytesIO()
    with zipfile.ZipFile(saida, "w", zipfile.ZIP_DEFLATED) as zipado:
        zipado.writestr("dados.json", json.dumps(dados, ensure_ascii=False, indent=2))
        zipado.writestr("memorias.md", memorias_em_texto(usuario, memorias, capitulos))
        for m in memorias:
            if m.foto_arquivo:
                arquivo = fotos.caminho(pasta_fotos, usuario.id, m.foto_arquivo)
                if arquivo.exists():
                    # já é JPEG: guarda sem comprimir de novo
                    zipado.write(arquivo, f"fotos/{m.id}.jpg", compress_type=zipfile.ZIP_STORED)
    return saida.getvalue()


# ---------- importar ----------

def _ler_zip(conteudo: bytes) -> tuple[dict, dict[str, bytes]]:
    if len(conteudo) > TAMANHO_MAXIMO_DO_ZIP:
        raise ArquivoInvalido("O arquivo passa de 500 MB.")
    try:
        zipado = zipfile.ZipFile(io.BytesIO(conteudo))
    except zipfile.BadZipFile:
        raise ArquivoInvalido("O arquivo não é um ZIP.") from None
    with zipado:
        if sum(i.file_size for i in zipado.infolist()) > TAMANHO_MAXIMO_DESCOMPACTADO:
            raise ArquivoInvalido("O conteúdo do ZIP é grande demais.")
        if "dados.json" not in zipado.namelist():
            raise ArquivoInvalido("O ZIP não tem o arquivo dados.json. Use um arquivo exportado pelo Vida em Semanas.")
        try:
            dados = json.loads(zipado.read("dados.json"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            raise ArquivoInvalido("O dados.json está corrompido.") from None
        # só lê nomes esperados; nada é extraído para o disco
        imagens = {nome[len("fotos/"):-len(".jpg")]: zipado.read(nome) for nome in zipado.namelist()
                   if nome.startswith("fotos/") and nome.endswith(".jpg") and nome.count("/") == 1}
    if not isinstance(dados, dict) or dados.get("formato") != FORMATO:
        raise ArquivoInvalido("Formato de arquivo desconhecido.")
    return dados, imagens


def _momento(texto: Any) -> datetime:
    try:
        return em_utc(datetime.fromisoformat(str(texto)))
    except ValueError:
        return datetime(1970, 1, 1, tzinfo=UTC)


class _Importador:
    def __init__(self, sessao: Session, usuario: Usuario, pasta_fotos: Path):
        self.sessao = sessao
        self.usuario = usuario
        self.pasta_fotos = pasta_fotos
        self.novos_ids: dict[str, str] = {}  # id do arquivo -> id nesta conta (quando precisou mudar)
        self.resumo: dict[str, dict[str, int]] = {}

    def contar(self, tipo: str, acao: str) -> None:
        self.resumo.setdefault(tipo, {"criados": 0, "atualizados": 0, "mantidos": 0, "recusados": 0})
        self.resumo[tipo][acao] += 1

    def id_local(self, id_do_arquivo: str) -> str:
        return self.novos_ids.get(id_do_arquivo, id_do_arquivo)

    def aplicar(self, modelo, item: dict, campos: dict[str, Any], tipo: str) -> Any | None:
        """Cria ou atualiza um registro. Devolve o registro gravado, ou None se nada mudou."""
        id_arquivo = str(item.get("id") or "")
        # já importado antes nesta conta com outro id? então é o mesmo registro
        existente = self.sessao.exec(select(modelo).where(
            modelo.usuario_id == self.usuario.id, modelo.id_de_origem == id_arquivo)).first() if id_arquivo else None
        if existente is not None:
            self.novos_ids[id_arquivo] = existente.id
        elif not ID_VALIDO.fullmatch(id_arquivo):
            # id fora do padrão (arquivo editado à mão ou malicioso): nunca é usado como está
            self.novos_ids[id_arquivo] = novo_id()
        else:
            existente = self.sessao.get(modelo, id_arquivo)
            if existente is not None and existente.usuario_id != self.usuario.id:
                existente = None  # o id é de outra conta: não tocar; usar um id novo
                self.novos_ids[id_arquivo] = novo_id()
        if existente is None:
            mudou = id_arquivo in self.novos_ids
            registro = modelo(id=self.id_local(id_arquivo), usuario_id=self.usuario.id, **campos,
                              id_de_origem=id_arquivo[:64] if mudou and id_arquivo else None,
                              criado_em=_momento(item.get("criado_em")), atualizado_em=_momento(item.get("atualizado_em")))
            self.sessao.add(registro)
            self.contar(tipo, "criados")
            return registro
        if existente.excluido_em is None and em_utc(existente.atualizado_em) >= _momento(item.get("atualizado_em")):
            self.contar(tipo, "mantidos")  # a versão da conta é a mais recente
            return None
        for campo, valor in campos.items():
            setattr(existente, campo, valor)
        existente.excluido_em = None
        existente.atualizado_em = _momento(item.get("atualizado_em"))
        self.sessao.add(existente)
        self.contar(tipo, "atualizados")
        return existente

    def importar(self, dados: dict, imagens: dict[str, bytes]) -> dict:
        perfil = dados.get("perfil") or {}
        perfil_usado = False
        if self.usuario.nascimento is None and perfil.get("sexo") in ("masculino", "feminino"):
            try:
                nascimento = date.fromisoformat(str(perfil.get("nascimento")))
            except ValueError:
                nascimento = None
            if nascimento and date(1900, 1, 1) <= nascimento <= date.today():
                self.usuario.nascimento = nascimento
                self.usuario.sexo = perfil["sexo"]
                self.sessao.add(self.usuario)
                perfil_usado = True

        for item in dados.get("capitulos", []):
            try:
                campos = CapituloDados.model_validate({k: item.get(k) for k in CapituloDados.model_fields if k in item}).model_dump()
            except ValidationError:
                self.contar("capitulos", "recusados")
                continue
            self.aplicar(Capitulo, item, campos, "capitulos")

        # memórias: primeiro sem as ligações, que podem apontar para memórias ainda não gravadas
        memorias: list[tuple[dict, Memoria | None]] = []
        for item in dados.get("memorias", []):
            try:
                valido = MemoriaDados.model_validate({**{k: item.get(k) for k in MemoriaDados.model_fields if k in item}, "veio_de": []})
            except ValidationError:
                self.contar("memorias", "recusados")
                continue
            memorias.append((item, self.aplicar(Memoria, item, valido.model_dump(), "memorias")))
        self.sessao.flush()

        minhas = {m.id for m in self.sessao.exec(select(Memoria).where(Memoria.usuario_id == self.usuario.id, Memoria.excluido_em.is_(None)))}
        for item, registro in memorias:
            if registro is None:
                continue
            ligacoes = [self.id_local(str(i)) for i in item.get("veio_de", []) if isinstance(i, str)]
            registro.veio_de = [i for i in dict.fromkeys(ligacoes) if i in minhas and i != registro.id]
            foto = imagens.get(str(item.get("id")))
            if foto:
                try:
                    jpeg = fotos.preparar(foto)  # limpa de novo: o arquivo pode ter sido editado
                    anterior = registro.foto_arquivo
                    registro.foto_arquivo = fotos.gravar(self.pasta_fotos, self.usuario.id, registro.id, jpeg)
                    if anterior:
                        fotos.apagar(self.pasta_fotos, self.usuario.id, anterior)
                except fotos.FotoInvalida:
                    self.contar("fotos", "recusados")
            self.sessao.add(registro)

        for item in dados.get("intencoes", []):
            try:
                campos = IntencaoDados.model_validate({k: item.get(k) for k in IntencaoDados.model_fields if k in item}).model_dump(mode="json")
            except ValidationError:
                self.contar("intencoes", "recusados")
                continue
            if campos.get("memoria_id"):
                local = self.id_local(campos["memoria_id"])
                campos["memoria_id"] = local if local in minhas else None
            self.aplicar(Intencao, item, campos, "intencoes")

        for item in dados.get("respostas_de_saude", []):
            respostas, resultado = item.get("respostas"), item.get("resultado")
            if (not isinstance(respostas, dict) or len(respostas) > 50 or not isinstance(resultado, dict)
                    or not all(isinstance(resultado.get(k), (int, float)) for k in CHAVES_DO_RESULTADO)):
                self.contar("respostas_de_saude", "recusados")
                continue
            numero = lambda x, minimo, maximo: x if isinstance(x, (int, float)) and minimo <= x <= maximo else None  # noqa: E731
            campos = {"respostas": {str(k)[:40]: str(v)[:40] for k, v in respostas.items()},
                      "resultado": {k: float(resultado[k]) for k in CHAVES_DO_RESULTADO},
                      "altura_m": numero(item.get("altura_m"), 1.0, 2.5), "peso_kg": numero(item.get("peso_kg"), 25, 350),
                      "versao_config": str(item.get("versao_config", "desconhecida"))[:60]}
            self.aplicar(RespostasDeSaude, item, campos, "respostas_de_saude")

        self.sessao.commit()
        return {"perfil_preenchido": perfil_usado, "resumo": self.resumo}


def importar(sessao: Session, usuario: Usuario, pasta_fotos: Path, conteudo: bytes) -> dict:
    dados, imagens = _ler_zip(conteudo)
    return _Importador(sessao, usuario, pasta_fotos).importar(dados, imagens)
