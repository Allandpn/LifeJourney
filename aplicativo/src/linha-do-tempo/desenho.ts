// Transforma as linhas (linhas.ts) em HTML. Só desenha: não guarda estado.

import type { Estimativa, Memoria } from "../tipos";
import { DIA, MESES, MESES_LONGOS, SEMANA, ano, formatarData, formatarNumero, idadeEm, semanaDeVida } from "../tempo";

/** "AAAA-MM-DD" de um instante, no fuso local. */
function iso(instante: number): string {
  const d = new Date(instante);
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
}
import {
  type CapituloNaLinha,
  type Granularidade,
  type IntencaoNaLinha,
  type Linha,
  type MemoriaNaLinha,
  corDaEpoca,
  destaques,
  meses,
  opacidadeDoFuturo,
  sobrevivenciaNaIdade,
} from "./linhas";

export interface Contexto {
  nascimento: number;
  hoje: number;
  granularidade: Granularidade;
  faixas: number;
  capitulos: CapituloNaLinha[];
  estimativa: Estimativa | null;
  memoriaPorId: Map<string, Memoria>;
  totalDeMemorias: number;
}

const LIMITE_NO_ANO = 3;
const ROTULO_STATUS: Record<string, string> = { ativa: "ativa", pausada: "pausada" };
const INTENSIDADE = ["leve", "média", "forte"];

/** Escapa texto do usuário antes de pôr no HTML. */
export function esc(texto: string): string {
  return texto.replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]!);
}

export function corCss(cor: string | null): string {
  return cor ? `var(--cap-${cor})` : "var(--texto-secundario)";
}

function corNaData(ctx: Contexto, instante: number): string {
  return corCss(corDaEpoca(ctx.capitulos, instante));
}

function espinha(linha: Linha, ctx: Contexto, no = ""): string {
  let fios = "";
  if (linha.capitulos.length) {
    for (let faixa = 0; faixa < ctx.faixas; faixa++) {
      const c = linha.capitulos.find((x) => x.faixa === faixa);
      const inicio = linha.tipo === "capitulo" && c === linha.capitulo ? ' class="inicio"' : "";
      fios += c ? `<i${inicio} style="color:${corCss(c.capitulo.cor)}"></i>` : "<i></i>";
    }
    fios = `<div class="fios">${fios}</div>`;
  }
  return `<div class="espinha">${fios}${no}</div>`;
}

function rotuloDoIntervalo(inicio: number, fim: number, ctx: Contexto, futuro: boolean): string {
  const a = new Date(inicio);
  const b = new Date(fim - (ctx.granularidade === "semana" ? SEMANA : DIA));
  const ya = a.getFullYear();
  const yb = Math.max(ya, b.getFullYear());
  if (futuro || ctx.granularidade === "ano") return ya === yb ? String(ya) : `${ya}–${yb}`;
  if (a.getMonth() === b.getMonth() && ya === yb) return `${MESES[a.getMonth()]} ${ya}`;
  return ya === yb ? `${MESES[a.getMonth()]}–${MESES[b.getMonth()]} ${ya}` : `${MESES[a.getMonth()]} ${ya} – ${MESES[b.getMonth()]} ${yb}`;
}

function rotuloDoPeriodo(p: { inicio: number; fim: number }, ctx: Contexto): [string, string] {
  const a = new Date(p.inicio);
  const b = new Date(p.fim - DIA);
  const idade = idadeEm(ctx.nascimento, Math.max(p.inicio, ctx.nascimento));
  // no nível ano, a idade que a pessoa completa naquele ano
  if (ctx.granularidade === "ano") return [String(a.getFullYear()), `${a.getFullYear() - new Date(ctx.nascimento).getFullYear()} anos`];
  if (ctx.granularidade === "mes") return [MESES_LONGOS[a.getMonth()], `${a.getFullYear()} · ${idade} anos`];
  const dias = a.getMonth() === b.getMonth()
    ? `${a.getDate()}–${b.getDate()} ${MESES[a.getMonth()]}`
    : `${a.getDate()} ${MESES[a.getMonth()]} – ${b.getDate()} ${MESES[b.getMonth()]}`;
  return [dias, `${a.getFullYear()} · semana ${formatarNumero(semanaDeVida(ctx.nascimento, p.inicio))}`];
}

function cartaoDeMemoria({ memoria, instante }: MemoriaNaLinha, ctx: Contexto): string {
  const origem = ctx.granularidade !== "ano" && memoria.veio_de.length ? ctx.memoriaPorId.get(memoria.veio_de[0]) : undefined;
  const emocao = memoria.emocao ? `<span class="emocao">${memoria.emocao}</span>` : "";
  const foto = memoria.foto ? `<img class="foto" src="${memoria.foto}" alt="" loading="lazy" decoding="async">` : "";
  return `<button type="button" class="cartao i${memoria.intensidade}${foto ? " com-foto" : ""}" data-memoria="${memoria.id}" style="--epoca:${corNaData(ctx, instante)}">
    ${foto}<span class="texto">${esc(memoria.texto)}</span>
    ${origem ? `<span class="origem">depois de: ${esc(origem.texto.slice(0, 46))}${origem.texto.length > 46 ? "…" : ""}</span>` : ""}
    <span class="meta">${emocao}${formatarData(instante)}</span>
  </button>`;
}

function cartaoDeIntencao({ intencao, instante }: IntencaoNaLinha): string {
  const h = intencao.horizonte;
  const quando = h.tipo === "intervalo"
    ? `entre ${h.de.slice(0, 4)} e ${h.ate.slice(0, 4)}`
    : instante !== null ? `${MESES[new Date(instante).getMonth()]} de ${ano(instante)}` : "sem data";
  return `<button type="button" class="intencao" data-intencao="${intencao.id}"><span class="texto">${esc(intencao.nome)}</span>
    <span class="meta">${quando} · ${ROTULO_STATUS[intencao.status] ?? intencao.status}</span></button>`;
}

function atributosDoFuturo(linha: Linha, ctx: Contexto): { classes: string; estilo: string } {
  if (!linha.futuro || !ctx.estimativa) return { classes: linha.futuro ? " futuro" : "", estilo: "" };
  const idade = (linha.inicio + linha.fim) / 2;
  const anos = (idade - ctx.nascimento) / (365.2425 * DIA);
  const opacidade = opacidadeDoFuturo(sobrevivenciaNaIdade(ctx.estimativa, anos));
  const tracejada = anos >= ctx.estimativa.p10 ? " tracejada" : "";
  return { classes: ` futuro${tracejada}`, estilo: ` style="--op:${opacidade.toFixed(2)}"` };
}

export function desenharLinha(linha: Linha, indice: number, ctx: Contexto): string {
  const { classes, estilo } = atributosDoFuturo(linha, ctx);
  const lado = "lado" in linha && linha.lado === "esquerda" ? " lado-esquerdo" : "";
  const abre = (tipo: string, extra = "") =>
    `<section class="linha ${tipo}${classes}${lado}" data-indice="${indice}"${estilo}${extra}>`;

  switch (linha.tipo) {
    case "borda":
      return `${abre(linha.tipo)}${espinha(linha, ctx)}<div class="nota">${esc(linha.texto)}</div></section>`;
    case "marco":
      return `${abre(linha.tipo)}${espinha(linha, ctx)}<div class="nota"><button type="button" class="marco-botao" data-estimativa>${esc(linha.texto)}</button></div></section>`;

    case "capitulo": {
      const c = linha.capitulo.capitulo;
      const periodo = `${c.inicio.slice(0, 4)} – ${c.fim ? c.fim.slice(0, 4) : "hoje"}`;
      return `${abre("abertura", ` style="--cap:${corCss(c.cor)}"`)}${espinha(linha, ctx)}
        <button type="button" class="abertura-titulo" data-capitulo="${c.id}"><span class="etiqueta">capítulo</span><strong>${esc(c.nome)}</strong></button>
        <div class="abertura-anos">${periodo}</div></section>`;
    }

    case "vazio": {
      const altura = Math.round(Math.min(92, 26 + 9 * Math.sqrt(meses(linha.inicio, linha.fim))));
      const a0 = idadeEm(ctx.nascimento, linha.inicio);
      const a1 = idadeEm(ctx.nascimento, linha.fim - DIA);
      const texto = linha.futuro
        ? `${rotuloDoIntervalo(linha.inicio, linha.fim, ctx, true)} · ${a0 === a1 ? a0 : `${a0} a ${a1}`} anos`
        : `${rotuloDoIntervalo(linha.inicio, linha.fim, ctx, false)} · nada registrado ainda`;
      const convite = linha.futuro ? "" : `<button type="button" class="lembrar" data-nova-memoria="${iso((linha.inicio + Math.min(linha.fim, ctx.hoje)) / 2)}">lembrar de algo</button>`;
      return `${abre("vazio")}${espinha(linha, ctx)}<div class="nota" style="min-height:${altura}px"><span>${texto}</span>${convite}</div></section>`;
    }

    case "algumDia":
      return `${abre("algum-dia")}${espinha(linha, ctx, '<span class="no aberto"></span>')}
        <header class="rotulo"><span class="grande">algum dia</span><span class="sub">sem data, sem pressa</span></header>
        <div class="corpo"><div class="sem-data">${linha.intencoes.map(cartaoDeIntencao).join("")}</div></div></section>`;

    case "hoje": {
      const hoje = new Date(ctx.hoje);
      const ecos = linha.ecos.length
        ? `<hr><span class="etiqueta">Nesta semana, em outros anos</span><ul class="ecos">${linha.ecos.map(({ memoria, instante }) =>
            `<li><button type="button" data-ir="${memoria.id}">${esc(memoria.texto)}<span>${ano(instante)} · há ${hoje.getFullYear() - ano(instante)} anos</span></button></li>`).join("")}</ul>`
        : "";
      const capitulos = linha.capitulos.map((c) => esc(c.capitulo.nome)).join(" · ");
      return `${abre("hoje")}${espinha(linha, ctx, '<span class="no"></span>')}
        <header class="rotulo"><span class="grande">Hoje</span><span class="sub">${hoje.getDate()} de ${MESES_LONGOS[hoje.getMonth()]} de ${hoje.getFullYear()}</span></header>
        <div class="corpo"><div class="cartao-hoje">
          <span class="etiqueta">semana</span>
          <div class="semana">${formatarNumero(semanaDeVida(ctx.nascimento, ctx.hoje))}</div>
          <p>da sua vida · ${idadeEm(ctx.nascimento, ctx.hoje)} anos${capitulos ? ` · ${capitulos}` : ""}</p>${ecos}
          ${ctx.totalDeMemorias === 0 ? '<hr><p class="convite">Que tal começar por 3 a 5 memórias marcantes? Sem pressa: o resto pode vir aos poucos.</p>' : ""}
          <div class="linha-de-botoes"><button type="button" class="botao" data-nova-memoria="${iso(ctx.hoje)}">Registrar algo de hoje</button>
            <button type="button" class="ligacao-discreta" data-estimativa>Como o futuro é estimado</button></div>
        </div>${linha.memorias.map((m) => cartaoDeMemoria(m, ctx)).join("")}</div></section>`;
    }

    case "periodo": {
      const [grande, sub] = rotuloDoPeriodo(linha.periodo, ctx);
      const memorias = ctx.granularidade === "ano" ? destaques(linha.memorias, LIMITE_NO_ANO) : linha.memorias;
      const resto = linha.memorias.length - memorias.length;
      const forte = linha.memorias.reduce<MemoriaNaLinha | null>((m, x) => (!m || x.memoria.intensidade > m.memoria.intensidade ? x : m), null);
      const no = forte
        ? `<span class="no n${forte.memoria.intensidade}" style="--epoca:${corNaData(ctx, forte.instante)}"></span>`
        : '<span class="no aberto"></span>';
      let corpo = memorias.map((m) => cartaoDeMemoria(m, ctx)).join("")
        + (resto ? `<button type="button" class="mais" data-ampliar="${linha.periodo.inicio}">+ ${resto} ${resto > 1 ? "memórias" : "memória"} neste ano</button>` : "")
        + linha.intencoes.map(cartaoDeIntencao).join("");
      if (!linha.memorias.length && !linha.intencoes.length) {
        corpo = `<button type="button" class="lembrar" data-nova-memoria="${iso(Math.min(linha.inicio, ctx.hoje))}">registrar algo desta semana</button>`;
      }
      return `${abre("periodo")}${espinha(linha, ctx, no)}
        <header class="rotulo"><span class="grande">${grande}</span><span class="sub">${sub}</span></header>
        <div class="corpo">${corpo}</div></section>`;
    }
  }
}

export function desenharDetalhe(memoria: Memoria, ctx: Contexto, instante: number): string {
  const capitulos = ctx.capitulos.filter((c) => c.inicio <= instante && instante < c.fim).map((c) => esc(c.capitulo.nome)).join(" · ");
  const ligacoes = [
    ...memoria.veio_de.map((id) => ["veio de", ctx.memoriaPorId.get(id)] as const),
    ...memoria.levou_a.map((id) => ["levou a", ctx.memoriaPorId.get(id)] as const),
  ].filter(([, m]) => m);
  return `${memoria.foto ? `<img class="foto-grande" src="${memoria.foto}" alt="">` : ""}
    <span class="etiqueta">${formatarData(instante)} · ${idadeEm(ctx.nascimento, instante)} anos · semana ${formatarNumero(semanaDeVida(ctx.nascimento, instante))}${capitulos ? ` · ${capitulos}` : ""}</span>
    <p class="texto-completo">${esc(memoria.texto)}</p>
    <div class="meta">${memoria.emocao ? `<span class="emocao" style="--epoca:${corNaData(ctx, instante)}">${memoria.emocao}</span>` : ""}intensidade ${INTENSIDADE[memoria.intensidade - 1]}${memoria.silenciar ? " · fora de “nesta semana”" : ""}</div>
    ${ligacoes.length ? `<div class="ligacoes">${ligacoes.map(([rotulo, m]) => `<button type="button" data-ir="${m!.id}"><span>${rotulo}</span>${esc(m!.texto)}</button>`).join("")}</div>` : ""}
    <div class="acoes"><button type="button" class="botao" data-editar-memoria="${memoria.id}">Editar</button><button type="button" class="botao" data-fechar>Fechar</button></div>`;
}
