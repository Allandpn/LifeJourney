// Monta as linhas da rolagem a partir dos dados. Só cálculo: nada aqui desenha na tela.
//
// A linha do tempo é uma lista de linhas, do nascimento até um pouco depois do
// percentil 90 da estimativa. Cada linha cobre um intervalo [inicio, fim) do tempo,
// o que permite converter a posição da rolagem em data e vice-versa.

import type { Capitulo, CorCapitulo, Estimativa, Intencao, Memoria } from "../tipos";
import { ANO, DIA, SEMANA, ano, inicioDoDia, instanteNaIdade, lerData } from "../tempo";

export type Granularidade = "ano" | "mes" | "semana";

/** Capítulo com datas já convertidas e a faixa (fio) que ocupa na linha. */
export interface CapituloNaLinha {
  capitulo: Capitulo;
  inicio: number;
  fim: number; // capítulo em andamento termina amanhã
  faixa: number;
}

export interface MemoriaNaLinha {
  memoria: Memoria;
  instante: number;
}

export interface IntencaoNaLinha {
  intencao: Intencao;
  instante: number | null; // null = "algum dia"
}

interface Base {
  inicio: number;
  fim: number;
  capitulos: CapituloNaLinha[]; // capítulos ativos no intervalo
  futuro: boolean;
}

export type Linha =
  | (Base & { tipo: "borda"; texto: string })
  | (Base & { tipo: "marco"; texto: string })
  | (Base & { tipo: "capitulo"; capitulo: CapituloNaLinha })
  | (Base & { tipo: "vazio" })
  | (Base & {
      tipo: "periodo";
      periodo: { inicio: number; fim: number }; // o período inteiro (ano, mês ou semana)
      memorias: MemoriaNaLinha[];
      intencoes: IntencaoNaLinha[];
      lado: "esquerda" | "direita";
    })
  | (Base & { tipo: "hoje"; memorias: MemoriaNaLinha[]; ecos: MemoriaNaLinha[] })
  | (Base & { tipo: "algumDia"; intencoes: IntencaoNaLinha[]; lado: "esquerda" | "direita" });

export interface Entrada {
  nascimento: number;
  hoje: number;
  memorias: Memoria[];
  capitulos: Capitulo[];
  intencoes: Intencao[];
  estimativa: Estimativa | null;
}

export interface LinhaDoTempo {
  linhas: Linha[];
  capitulos: CapituloNaLinha[];
  faixas: number; // quantos fios de capítulo existem lado a lado
  fim: number; // instante em que a rolagem termina
  idadeFinal: number; // em anos, para o minimapa
  memorias: MemoriaNaLinha[];
  intencoes: IntencaoNaLinha[];
}

const ANOS_ALEM_DO_P90 = 3;
const IDADE_FINAL_SEM_ESTIMATIVA = 100;

// ---------- capítulos ----------

/** Distribui os capítulos em faixas paralelas: dois capítulos na mesma faixa nunca se sobrepõem.
 * Os principais são distribuídos primeiro, para ficarem nos fios mais à esquerda. */
export function distribuirCapitulos(capitulos: Capitulo[], hoje: number): CapituloNaLinha[] {
  const ordenados = capitulos
    .map((c) => ({
      capitulo: c,
      inicio: lerData(c.inicio),
      fim: c.fim ? lerData(c.fim) + DIA : inicioDoDia(hoje) + DIA,
      faixa: 0,
    }))
    .sort((a, b) => Number(b.capitulo.principal) - Number(a.capitulo.principal) || a.inicio - b.inicio);

  const ocupadas: CapituloNaLinha[][] = [];
  for (const c of ordenados) {
    let faixa = ocupadas.findIndex((lista) => lista.every((o) => o.fim <= c.inicio || o.inicio >= c.fim));
    if (faixa === -1) {
      faixa = ocupadas.length;
      ocupadas.push([]);
    }
    ocupadas[faixa].push(c);
    c.faixa = faixa;
  }
  return ordenados.sort((a, b) => a.inicio - b.inicio);
}

export function capitulosEntre(capitulos: CapituloNaLinha[], inicio: number, fim: number): CapituloNaLinha[] {
  return capitulos.filter((c) => c.inicio < fim && c.fim > inicio);
}

/** O capítulo que define a cor da época: o principal ativo que começou primeiro. */
export function capituloDaEpoca(capitulos: CapituloNaLinha[], instante: number): CapituloNaLinha | null {
  const ativos = capitulos.filter((c) => c.capitulo.principal && c.inicio <= instante && instante < c.fim);
  ativos.sort((a, b) => a.inicio - b.inicio);
  return ativos[0] ?? null;
}

export function corDaEpoca(capitulos: CapituloNaLinha[], instante: number): CorCapitulo | null {
  return capituloDaEpoca(capitulos, instante)?.capitulo.cor ?? null;
}

// ---------- intenções ----------

/** Onde a intenção aparece: na data, no meio do intervalo, ou sem data ("algum dia").
 * Intenções que viraram memória ou foram deixadas de lado não aparecem. */
export function posicionarIntencoes(intencoes: Intencao[]): IntencaoNaLinha[] {
  return intencoes
    .filter((i) => i.status === "ativa" || i.status === "pausada")
    .map((i) => {
      const h = i.horizonte;
      if (h.tipo === "data") return { intencao: i, instante: lerData(h.data) };
      if (h.tipo === "intervalo") return { intencao: i, instante: (lerData(h.de) + lerData(h.ate)) / 2 };
      return { intencao: i, instante: null };
    });
}

// ---------- períodos ----------

/** Intervalos de cada ano, mês ou semana de vida, do nascimento até `fim`.
 * O dia de hoje vira um período próprio, para ter a sua linha na rolagem. */
export function periodos(
  granularidade: Granularidade,
  nascimento: number,
  fim: number,
  hoje: number,
): { inicio: number; fim: number; hoje?: boolean; inteiro: { inicio: number; fim: number } }[] {
  const brutos: { inicio: number; fim: number }[] = [];
  if (granularidade === "semana") {
    for (let t = nascimento; t < fim; t += SEMANA) brutos.push({ inicio: t, fim: t + SEMANA });
  } else {
    const n = new Date(nascimento);
    let cursor = granularidade === "ano" ? new Date(n.getFullYear(), 0, 1) : new Date(n.getFullYear(), n.getMonth(), 1);
    while (cursor.getTime() < fim) {
      const proximo =
        granularidade === "ano"
          ? new Date(cursor.getFullYear() + 1, 0, 1)
          : new Date(cursor.getFullYear(), cursor.getMonth() + 1, 1);
      brutos.push({ inicio: Math.max(cursor.getTime(), nascimento), fim: proximo.getTime() });
      cursor = proximo;
    }
  }

  const diaDeHoje = inicioDoDia(hoje);
  const resultado: ReturnType<typeof periodos> = [];
  for (const p of brutos) {
    if (p.inicio <= diaDeHoje && diaDeHoje < p.fim) {
      if (p.inicio < diaDeHoje) resultado.push({ inicio: p.inicio, fim: diaDeHoje, inteiro: p });
      resultado.push({ inicio: diaDeHoje, fim: diaDeHoje + DIA, hoje: true, inteiro: p });
      if (diaDeHoje + DIA < p.fim) resultado.push({ inicio: diaDeHoje + DIA, fim: p.fim, inteiro: p });
    } else {
      resultado.push({ ...p, inteiro: p });
    }
  }
  return resultado;
}

// ---------- memórias ----------

/** As memórias de mais destaque de um período, mantidas em ordem de data. */
export function destaques(memorias: MemoriaNaLinha[], limite: number): MemoriaNaLinha[] {
  if (memorias.length <= limite) return memorias;
  return [...memorias]
    .sort(
      (a, b) =>
        Number(b.memoria.marcante) - Number(a.memoria.marcante) ||
        b.memoria.intensidade - a.memoria.intensidade ||
        a.instante - b.instante,
    )
    .slice(0, limite)
    .sort((a, b) => a.instante - b.instante);
}

/** Memórias de outros anos que caíram a até 3 dias da data de hoje.
 * As marcadas como "não me lembrar disto" (silenciar) nunca entram. */
export function ecosDeHoje(memorias: MemoriaNaLinha[], hoje: number): MemoriaNaLinha[] {
  const h = new Date(hoje);
  return memorias.filter(({ memoria, instante }) => {
    const d = new Date(instante);
    if (memoria.silenciar || d.getFullYear() === h.getFullYear()) return false;
    return [-1, 0, 1].some((desloca) => {
      const mesmoDia = new Date(h.getFullYear() + desloca, d.getMonth(), d.getDate()).getTime();
      return Math.abs(mesmoDia - inicioDoDia(hoje)) <= 3 * DIA;
    });
  });
}

// ---------- futuro ----------

/** Chance de estar vivo numa idade, interpolando a curva da estimativa. */
export function sobrevivenciaNaIdade(estimativa: Estimativa | null, idade: number): number {
  if (!estimativa) return 1;
  const curva = estimativa.sobrevivencia;
  if (idade <= curva[0][0]) return 1;
  for (let i = 1; i < curva.length; i++) {
    const [x1, s1] = curva[i];
    if (idade <= x1) {
      const [x0, s0] = curva[i - 1];
      return s0 + ((idade - x0) / (x1 - x0)) * (s1 - s0);
    }
  }
  return 0;
}

/** Quão visível fica o futuro: inteiro até o P10 e esmaecendo com a chance de estar vivo. */
export function opacidadeDoFuturo(sobrevivencia: number): number {
  return 0.28 + 0.72 * Math.min(1, sobrevivencia / 0.9);
}

function marcos(nascimento: number, e: Estimativa | null): { instante: number; texto: string }[] {
  if (!e) return [];
  const arredonda = (x: number) => Math.round(x);
  return [
    { instante: instanteNaIdade(nascimento, e.p10), texto: `${arredonda(e.p10)} anos · daqui em diante a estimativa vira uma faixa` },
    { instante: instanteNaIdade(nascimento, e.mediana), texto: `${arredonda(e.mediana)} anos · meio da faixa estimada` },
    { instante: instanteNaIdade(nascimento, e.p90), texto: `${arredonda(e.p90)} anos · além daqui continua possível` },
  ];
}

// ---------- montagem ----------

export function montarLinhaDoTempo(entrada: Entrada, granularidade: Granularidade): LinhaDoTempo {
  const { nascimento, hoje, estimativa } = entrada;
  const idadeFinal = estimativa ? Math.ceil(estimativa.p90 + ANOS_ALEM_DO_P90) : IDADE_FINAL_SEM_ESTIMATIVA;
  const fim = instanteNaIdade(nascimento, idadeFinal);
  const capitulos = distribuirCapitulos(entrada.capitulos, hoje);
  const faixas = capitulos.reduce((m, c) => Math.max(m, c.faixa + 1), 0);

  const memorias: MemoriaNaLinha[] = entrada.memorias
    .map((m) => ({ memoria: m, instante: lerData(m.data) }))
    .sort((a, b) => a.instante - b.instante);
  const intencoes = posicionarIntencoes(entrada.intencoes);
  const comData = intencoes.filter((i) => i.instante !== null).sort((a, b) => a.instante! - b.instante!);
  const semData = intencoes.filter((i) => i.instante === null);
  const ultimaIntencao = comData.length ? comData[comData.length - 1].instante! : inicioDoDia(hoje);

  type Item = { instante: number } & ({ memoria: MemoriaNaLinha } | { intencao: IntencaoNaLinha });
  const itens: Item[] = [
    ...memorias.map((m) => ({ instante: m.instante, memoria: m })),
    ...comData.map((i) => ({ instante: i.instante!, intencao: i })),
  ].sort((a, b) => a.instante - b.instante);

  const linhas: Linha[] = [
    { tipo: "borda", inicio: nascimento, fim: nascimento, capitulos: [], futuro: false,
      texto: `${new Date(nascimento).toLocaleDateString("pt-BR", { day: "numeric", month: "long", year: "numeric" })} · a linha começa aqui` },
  ];
  const listaDeMarcos = marcos(nascimento, estimativa);
  let proximoMarco = 0;
  let proximoItem = 0;
  let vazioAtual: (Linha & { tipo: "vazio" }) | null = null;
  let chaveDoVazio = "";
  let algumDiaColocado = semData.length === 0;
  let lado = 0;
  const iniciados = new Set<string>();
  const diaDeHoje = inicioDoDia(hoje);

  for (const p of periodos(granularidade, nascimento, fim, hoje)) {
    const doPeriodo: Item[] = [];
    while (proximoItem < itens.length && itens[proximoItem].instante < p.fim) doPeriodo.push(itens[proximoItem++]);
    const ativos = capitulosEntre(capitulos, p.inicio, p.fim);
    const futuro = p.inicio > diaDeHoje;

    while (proximoMarco < listaDeMarcos.length && listaDeMarcos[proximoMarco].instante <= p.inicio) {
      linhas.push({ tipo: "marco", inicio: p.inicio, fim: p.inicio, capitulos: [], futuro: true, texto: listaDeMarcos[proximoMarco].texto });
      proximoMarco++;
      vazioAtual = null;
    }
    for (const c of ativos) {
      if (!iniciados.has(c.capitulo.id)) {
        linhas.push({ tipo: "capitulo", inicio: p.inicio, fim: p.inicio, capitulos: ativos, futuro, capitulo: c });
        vazioAtual = null;
      }
      iniciados.add(c.capitulo.id);
    }

    if (p.hoje) {
      const hojeMem = doPeriodo.flatMap((i) => ("memoria" in i ? [i.memoria] : []));
      linhas.push({ tipo: "hoje", inicio: p.inicio, fim: p.fim, capitulos: ativos, futuro: false, memorias: hojeMem, ecos: ecosDeHoje(memorias, hoje) });
      vazioAtual = null;
      continue;
    }

    const recente = granularidade === "semana" && !futuro && diaDeHoje - p.fim < 3 * SEMANA;
    if (doPeriodo.length === 0 && !recente) {
      // períodos vazios seguidos, com os mesmos capítulos, viram uma só faixa fina
      // no futuro, agrupa de 5 em 5 anos para manter a noção de distância
      const balde = futuro ? `f${Math.floor(ano(p.inicio) / 5)}-${proximoMarco}` : "";
      const chave = ativos.map((c) => c.capitulo.id).join() + "|" + balde;
      if (vazioAtual && chave === chaveDoVazio) {
        vazioAtual.fim = p.fim;
      } else {
        vazioAtual = { tipo: "vazio", inicio: p.inicio, fim: p.fim, capitulos: ativos, futuro };
        chaveDoVazio = chave;
        linhas.push(vazioAtual);
      }
      continue;
    }

    vazioAtual = null;
    linhas.push({
      tipo: "periodo", inicio: p.inicio, fim: p.fim, periodo: p.inteiro, capitulos: ativos, futuro,
      memorias: doPeriodo.flatMap((i) => ("memoria" in i ? [i.memoria] : [])),
      intencoes: doPeriodo.flatMap((i) => ("intencao" in i ? [i.intencao] : [])),
      lado: lado++ % 2 ? "esquerda" : "direita",
    });
    if (!algumDiaColocado && futuro && ultimaIntencao >= p.inicio && ultimaIntencao < p.fim) {
      linhas.push({ tipo: "algumDia", inicio: p.fim, fim: p.fim, capitulos: [], futuro: true, intencoes: semData, lado: lado++ % 2 ? "esquerda" : "direita" });
      algumDiaColocado = true;
    }
  }

  if (!algumDiaColocado) {
    // sem intenções datadas no futuro: "algum dia" vem logo depois de hoje
    const i = linhas.findIndex((l) => l.tipo === "hoje");
    const depois = linhas[i];
    linhas.splice(i + 1, 0, { tipo: "algumDia", inicio: depois.fim, fim: depois.fim, capitulos: [], futuro: true, intencoes: semData, lado: "direita" });
  }
  linhas.push({ tipo: "borda", inicio: fim, fim, capitulos: [], futuro: true, texto: "A linha segue além daqui, só mais tênue." });

  return { linhas, capitulos, faixas, fim, idadeFinal, memorias, intencoes };
}

/** Duração aproximada de um intervalo em meses, para dar altura às faixas vazias. */
export function meses(inicio: number, fim: number): number {
  return (fim - inicio) / (ANO / 12);
}
