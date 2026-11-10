// A vida inteira em semanas, desenhada num <canvas>: 52 colunas por ano de idade.

import { ANO } from "../tempo";
import { type LinhaDoTempo, corDaEpoca, opacidadeDoFuturo, sobrevivenciaNaIdade } from "../linha-do-tempo/linhas";
import type { Estimativa } from "../tipos";

export interface DadosDoMinimapa {
  nascimento: number;
  hoje: number;
  linha: LinhaDoTempo;
  estimativa: Estimativa | null;
}

const COLUNAS = 52;

export function desenharMinimapa(canvas: HTMLCanvasElement, d: DadosDoMinimapa): void {
  const caixa = canvas.getBoundingClientRect();
  if (!caixa.width || !caixa.height) return;
  const escala = window.devicePixelRatio || 1;
  canvas.width = Math.round(caixa.width * escala);
  canvas.height = Math.round(caixa.height * escala);
  const g = canvas.getContext("2d")!;
  g.setTransform(escala, 0, 0, escala, 0, 0);
  g.clearRect(0, 0, caixa.width, caixa.height);

  const estilo = getComputedStyle(document.documentElement);
  const cor = (nome: string) => estilo.getPropertyValue(nome).trim();
  const anos = d.linha.idadeFinal;
  const largura = caixa.width / COLUNAS;
  const altura = caixa.height / anos;
  const semanaDe = (t: number) => Math.floor(((t - d.nascimento) / ANO) * COLUNAS);
  const comMemoria = new Set(d.linha.memorias.map((m) => semanaDe(m.instante)));
  const comIntencao = new Set(d.linha.intencoes.flatMap((i) => (i.instante === null ? [] : [semanaDe(i.instante)])));
  const semanaDeHoje = semanaDe(d.hoje);
  const w = Math.max(largura - 0.5, 0.8);
  const h = Math.max(altura - 1, 1);

  for (let linha = 0; linha < anos; linha++) {
    for (let coluna = 0; coluna < COLUNAS; coluna++) {
      const k = linha * COLUNAS + coluna;
      const t = d.nascimento + (k / COLUNAS) * ANO;
      if (k <= semanaDeHoje) {
        const epoca = corDaEpoca(d.linha.capitulos, t);
        if (comMemoria.has(k)) [g.globalAlpha, g.fillStyle] = [1, cor("--texto")];
        else if (epoca) [g.globalAlpha, g.fillStyle] = [0.8, cor(`--cap-${epoca}`)];
        else [g.globalAlpha, g.fillStyle] = [1, cor("--linha")];
      } else if (comIntencao.has(k)) {
        [g.globalAlpha, g.fillStyle] = [1, cor("--destaque")];
      } else {
        const op = opacidadeDoFuturo(sobrevivenciaNaIdade(d.estimativa, k / COLUNAS));
        [g.globalAlpha, g.fillStyle] = [0.3 * op, cor("--texto-secundario")];
      }
      g.fillRect(coluna * largura, linha * altura, w, h);
    }
  }
  g.globalAlpha = 1;
  g.fillStyle = cor("--destaque");
  g.fillRect((semanaDeHoje % COLUNAS) * largura - 1, Math.floor(semanaDeHoje / COLUNAS) * altura - 1, w + 2, h + 2);
}
