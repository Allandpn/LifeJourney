import { describe, expect, it } from "vitest";
import type { Capitulo, Estimativa, Intencao, Memoria } from "../tipos";
import { lerData } from "../tempo";
import {
  capituloDaEpoca,
  destaques,
  distribuirCapitulos,
  ecosDeHoje,
  montarLinhaDoTempo,
  opacidadeDoFuturo,
  periodos,
  posicionarIntencoes,
  sobrevivenciaNaIdade,
  type Entrada,
  type Linha,
} from "./linhas";

const HOJE = lerData("2026-11-10");
const NASCIMENTO = lerData("1990-03-14");

function memoria(data: string, campos: Partial<Memoria> = {}): Memoria {
  return {
    id: data, data, texto: `Memória de ${data}`, emocao: null, intensidade: 2,
    marcante: false, silenciar: false, veio_de: [], levou_a: [], tags: [], foto: null, ...campos,
  };
}

function capitulo(id: string, inicio: string, fim: string | null, principal = true): Capitulo {
  return { id, nome: id, inicio, fim, cor: "azul", principal, categoria: null, notas: null };
}

function intencao(id: string, horizonte: Intencao["horizonte"], status: Intencao["status"] = "ativa"): Intencao {
  return { id, nome: id, horizonte, status, notas: null, memoria_id: null };
}

const ESTIMATIVA: Estimativa = {
  base: "brasileiro_medio", versao_config: "teste", hr_total: 1, expectativa_media: 81,
  p10: 62, mediana: 84, p90: 97,
  sobrevivencia: [[36.7, 1], [62, 0.9], [84, 0.5], [97, 0.1], [110, 0]],
};

function entrada(campos: Partial<Entrada> = {}): Entrada {
  return { nascimento: NASCIMENTO, hoje: HOJE, memorias: [], capitulos: [], intencoes: [], estimativa: ESTIMATIVA, ...campos };
}

function doTipo<T extends Linha["tipo"]>(linhas: Linha[], tipo: T) {
  return linhas.filter((l): l is Extract<Linha, { tipo: T }> => l.tipo === tipo);
}

describe("periodos", () => {
  it("separa o dia de hoje num período próprio", () => {
    const lista = periodos("ano", NASCIMENTO, lerData("2030-01-01"), HOJE);
    const hoje = lista.filter((p) => p.hoje);
    expect(hoje).toHaveLength(1);
    expect(hoje[0].inicio).toBe(HOJE);
    const de2026 = lista.filter((p) => p.inteiro.inicio === lerData("2026-01-01"));
    expect(de2026.map((p) => !!p.hoje)).toEqual([false, true, false]);
  });

  it("o primeiro ano começa no nascimento, não em 1º de janeiro", () => {
    expect(periodos("ano", NASCIMENTO, lerData("1992-01-01"), HOJE)[0].inicio).toBe(NASCIMENTO);
  });

  it("os períodos cobrem o tempo sem buracos", () => {
    const lista = periodos("mes", NASCIMENTO, lerData("2030-01-01"), HOJE);
    for (let i = 1; i < lista.length; i++) expect(lista[i].inicio).toBe(lista[i - 1].fim);
  });
});

describe("capítulos", () => {
  it("capítulos sobrepostos ficam em faixas diferentes, e principais primeiro", () => {
    const lista = distribuirCapitulos([
      capitulo("namoro", "2015-01-01", "2020-01-01", false),
      capitulo("trabalho", "2014-01-01", "2018-01-01"),
      capitulo("estudio", "2018-01-02", null),
    ], HOJE);
    const faixa = Object.fromEntries(lista.map((c) => [c.capitulo.id, c.faixa]));
    expect(faixa).toEqual({ trabalho: 0, estudio: 0, namoro: 1 });
  });

  it("a cor da época é a do capítulo principal que começou primeiro", () => {
    const lista = distribuirCapitulos([
      capitulo("a", "2010-01-01", null),
      capitulo("b", "2015-01-01", null),
      capitulo("secundario", "2005-01-01", null, false),
    ], HOJE);
    expect(capituloDaEpoca(lista, lerData("2016-01-01"))?.capitulo.id).toBe("a");
    expect(capituloDaEpoca(lista, lerData("2006-01-01"))).toBeNull();
  });

  it("capítulo em andamento vai até hoje", () => {
    const [c] = distribuirCapitulos([capitulo("a", "2020-01-01", null)], HOJE);
    expect(c.fim).toBeGreaterThan(HOJE);
  });
});

describe("intenções", () => {
  it("datas, intervalos e algum dia", () => {
    const lista = posicionarIntencoes([
      intencao("d", { tipo: "data", data: "2027-04-01" }),
      intencao("i", { tipo: "intervalo", de: "2027-01-01", ate: "2029-01-01" }),
      intencao("a", { tipo: "algum_dia" }),
      intencao("feita", { tipo: "algum_dia" }, "virou_memoria"),
      intencao("largada", { tipo: "algum_dia" }, "deixada_de_lado"),
      intencao("pausa", { tipo: "algum_dia" }, "pausada"),
    ]);
    expect(lista.map((i) => i.intencao.id)).toEqual(["d", "i", "a", "pausa"]);
    expect(lista[1].instante).toBe((lerData("2027-01-01") + lerData("2029-01-01")) / 2);
    expect(lista[2].instante).toBeNull();
  });
});

describe("memórias", () => {
  it("destaques priorizam marcantes e intensas, mantendo a ordem de data", () => {
    const lista = ["2010-01-01", "2010-02-01", "2010-03-01", "2010-04-01"].map((d, i) => ({
      memoria: memoria(d, { intensidade: (i === 1 ? 3 : 1) as 1 | 3, marcante: i === 3 }),
      instante: lerData(d),
    }));
    expect(destaques(lista, 2).map((m) => m.memoria.id)).toEqual(["2010-02-01", "2010-04-01"]);
  });

  it("ecos: mesma época do ano em outros anos, sem as silenciadas", () => {
    const lista = [
      memoria("2015-11-08"), memoria("2021-11-12"), memoria("2021-11-20"),
      memoria("2019-11-10", { silenciar: true }), memoria("2026-11-09"),
    ].map((m) => ({ memoria: m, instante: lerData(m.data) }));
    expect(ecosDeHoje(lista, HOJE).map((m) => m.memoria.id)).toEqual(["2015-11-08", "2021-11-12"]);
  });

  it("ecos atravessam a virada do ano", () => {
    const lista = [{ memoria: memoria("2020-12-30"), instante: lerData("2020-12-30") }];
    expect(ecosDeHoje(lista, lerData("2027-01-01"))).toHaveLength(1);
  });
});

describe("futuro", () => {
  it("sobrevivência interpolada e opacidade", () => {
    expect(sobrevivenciaNaIdade(ESTIMATIVA, 50)).toBeCloseTo(1 - (0.1 * (50 - 36.7)) / (62 - 36.7));
    expect(sobrevivenciaNaIdade(ESTIMATIVA, 200)).toBe(0);
    expect(opacidadeDoFuturo(1)).toBe(1);
    expect(opacidadeDoFuturo(0.9)).toBe(1);
    expect(opacidadeDoFuturo(0)).toBeCloseTo(0.28);
  });
});

describe("montarLinhaDoTempo", () => {
  it("começa no nascimento, tem um só 'hoje' e termina depois do P90", () => {
    const { linhas, fim, idadeFinal } = montarLinhaDoTempo(entrada(), "ano");
    expect(linhas[0]).toMatchObject({ tipo: "borda", inicio: NASCIMENTO });
    expect(doTipo(linhas, "hoje")).toHaveLength(1);
    expect(idadeFinal).toBe(100);
    expect(linhas[linhas.length - 1]).toMatchObject({ tipo: "borda", inicio: fim });
  });

  it("as linhas ficam em ordem de tempo", () => {
    const { linhas } = montarLinhaDoTempo(entrada({ memorias: [memoria("2001-02-05"), memoria("2018-11-05")] }), "mes");
    for (let i = 1; i < linhas.length; i++) expect(linhas[i].inicio).toBeGreaterThanOrEqual(linhas[i - 1].inicio);
  });

  it("cada memória cai no período certo", () => {
    const { linhas } = montarLinhaDoTempo(entrada({ memorias: [memoria("2001-02-05"), memoria("2001-09-01")] }), "mes");
    const comMemorias = doTipo(linhas, "periodo").filter((l) => l.memorias.length);
    expect(comMemorias.map((l) => new Date(l.inicio).getMonth())).toEqual([1, 8]);
  });

  it("anos seguidos sem nada viram uma faixa só", () => {
    const { linhas } = montarLinhaDoTempo(entrada({ memorias: [memoria("1995-06-01"), memoria("2005-06-01")] }), "ano");
    const vazios = doTipo(linhas, "vazio").filter((l) => !l.futuro);
    const entre = vazios.find((l) => l.inicio === lerData("1996-01-01"));
    expect(entre?.fim).toBe(lerData("2005-01-01"));
  });

  it("no nível mês, anos vazios seguidos também viram uma faixa só", () => {
    const { linhas } = montarLinhaDoTempo(entrada({ memorias: [memoria("1995-06-01"), memoria("2005-06-01")] }), "mes");
    const entre = doTipo(linhas, "vazio").find((l) => l.inicio === lerData("1995-07-01"));
    expect(entre?.fim).toBe(lerData("2005-06-01"));
  });

  it("vazios não atravessam o começo de um capítulo", () => {
    const { linhas } = montarLinhaDoTempo(entrada({ capitulos: [capitulo("c", "2000-03-01", "2003-01-01")] }), "ano");
    const indice = linhas.findIndex((l) => l.tipo === "capitulo");
    expect(linhas[indice - 1].fim).toBeLessThanOrEqual(lerData("2000-01-01"));
  });

  it("marca o começo de cada capítulo uma vez", () => {
    const { linhas } = montarLinhaDoTempo(entrada({
      capitulos: [capitulo("a", "1990-03-14", "2001-01-31"), capitulo("b", "2001-02-01", null)],
    }), "semana");
    expect(doTipo(linhas, "capitulo").map((l) => l.capitulo.capitulo.id)).toEqual(["a", "b"]);
  });

  it("os três marcos da estimativa aparecem no futuro, em ordem", () => {
    const { linhas } = montarLinhaDoTempo(entrada(), "ano");
    expect(doTipo(linhas, "marco").map((l) => l.texto.split(" ")[0])).toEqual(["62", "84", "97"]);
  });

  it("'algum dia' vem depois da última intenção com data", () => {
    const { linhas } = montarLinhaDoTempo(entrada({
      intencoes: [intencao("j", { tipo: "data", data: "2030-05-01" }), intencao("x", { tipo: "algum_dia" })],
    }), "ano");
    const iData = linhas.findIndex((l) => l.tipo === "periodo" && l.intencoes.length > 0);
    const iAlgum = linhas.findIndex((l) => l.tipo === "algumDia");
    expect(iAlgum).toBe(iData + 1);
  });

  it("sem intenções com data, 'algum dia' vem logo depois de hoje", () => {
    const { linhas } = montarLinhaDoTempo(entrada({ intencoes: [intencao("x", { tipo: "algum_dia" })] }), "ano");
    const iHoje = linhas.findIndex((l) => l.tipo === "hoje");
    expect(linhas[iHoje + 1].tipo).toBe("algumDia");
  });

  it("na granularidade semana, as semanas recentes aparecem mesmo vazias", () => {
    const { linhas } = montarLinhaDoTempo(entrada(), "semana");
    const iHoje = linhas.findIndex((l) => l.tipo === "hoje");
    expect(linhas.slice(iHoje - 3, iHoje).every((l) => l.tipo === "periodo")).toBe(true);
  });

  it("sem estimativa, a linha vai até os 100 anos e não tem marcos", () => {
    const { linhas, idadeFinal } = montarLinhaDoTempo(entrada({ estimativa: null }), "ano");
    expect(idadeFinal).toBe(100);
    expect(doTipo(linhas, "marco")).toHaveLength(0);
  });
});
