// A tela da linha do tempo: desenha as linhas, liga a rolagem ao minimapa e ao
// cabeçalho, e responde aos toques.

import type { Capitulo, Estimativa, Intencao, Memoria } from "../tipos";
import { ano, idadeEm, inicioDoDia, lerData } from "../tempo";
import { desenharMinimapa } from "../minimapa/minimapa";
import { type Contexto, corCss, desenharDetalhe, desenharLinha, esc } from "./desenho";
import { type Granularidade, type LinhaDoTempo, capitulosEntre, montarLinhaDoTempo } from "./linhas";

export interface Dados {
  nascimento: string;
  memorias: Memoria[];
  capitulos: Capitulo[];
  intencoes: Intencao[];
  estimativa: Estimativa | null;
}

interface Medida {
  topo: number;
  altura: number;
}

const GUARDAR_GRANULARIDADE = "lj-granularidade";
const movimentoReduzido = () => window.matchMedia("(prefers-reduced-motion: reduce)").matches;

export class TelaDaLinhaDoTempo {
  private granularidade: Granularidade = "ano";
  private linha!: LinhaDoTempo;
  private medidas: Medida[] = [];
  private agendado = false;
  private readonly nascimento: number;
  private readonly hoje = inicioDoDia(Date.now());
  private readonly memoriaPorId: Map<string, Memoria>;

  constructor(
    private readonly el: {
      lista: HTMLElement;
      contexto: HTMLElement;
      cabecalho: HTMLElement;
      minimapa: HTMLElement;
      canvas: HTMLCanvasElement;
      visor: HTMLElement;
      dialogo: HTMLDialogElement;
      conteudoDoDialogo: HTMLElement;
      botoesDeGranularidade: HTMLButtonElement[];
      botaoHoje: HTMLButtonElement;
    },
    private readonly dados: Dados,
  ) {
    this.nascimento = lerData(dados.nascimento);
    this.memoriaPorId = new Map(dados.memorias.map((m) => [m.id, m]));
    try {
      const salva = localStorage.getItem(GUARDAR_GRANULARIDADE) as Granularidade | null;
      if (salva === "ano" || salva === "mes" || salva === "semana") this.granularidade = salva;
    } catch {
      // armazenamento indisponível: fica o padrão
    }
    this.ligarEventos();
  }

  iniciar(): void {
    this.desenhar();
    this.irParaHoje(false);
  }

  // ---------- desenho ----------

  private contexto(): Contexto {
    return {
      nascimento: this.nascimento, hoje: this.hoje, granularidade: this.granularidade,
      faixas: this.linha.faixas, capitulos: this.linha.capitulos, estimativa: this.dados.estimativa,
      memoriaPorId: this.memoriaPorId,
    };
  }

  private desenhar(): void {
    this.linha = montarLinhaDoTempo({ ...this.dados, nascimento: this.nascimento, hoje: this.hoje }, this.granularidade);
    const ctx = this.contexto();
    this.el.lista.dataset.granularidade = this.granularidade;
    this.el.lista.innerHTML = this.linha.linhas.map((l, i) => desenharLinha(l, i, ctx)).join("");
    for (const b of this.el.botoesDeGranularidade) b.setAttribute("aria-pressed", String(b.dataset.granularidade === this.granularidade));
    this.medir();
    this.desenharMinimapa();
    this.aoRolar();
  }

  private desenharMinimapa(): void {
    desenharMinimapa(this.el.canvas, { nascimento: this.nascimento, hoje: this.hoje, linha: this.linha, estimativa: this.dados.estimativa });
  }

  private medir(): void {
    const filhos = this.el.lista.children;
    this.medidas = Array.from(filhos, (f) => {
      const caixa = f.getBoundingClientRect();
      return { topo: caixa.top + window.scrollY, altura: caixa.height };
    });
    document.documentElement.style.setProperty("--altura-cabecalho", `${this.el.cabecalho.offsetHeight}px`);
  }

  // ---------- posição da rolagem <-> data ----------

  private dataNaPosicao(y: number): number {
    const m = this.medidas;
    let baixo = 0;
    let alto = m.length - 1;
    while (baixo < alto) {
      const meio = (baixo + alto + 1) >> 1;
      if (m[meio].topo <= y) baixo = meio;
      else alto = meio - 1;
    }
    const linha = this.linha.linhas[baixo];
    const fracao = Math.min(1, Math.max(0, (y - m[baixo].topo) / (m[baixo].altura || 1)));
    return linha.inicio + fracao * (linha.fim - linha.inicio);
  }

  private posicaoDaData(t: number): number {
    const linhas = this.linha.linhas;
    for (let i = 0; i < linhas.length; i++) {
      const l = linhas[i];
      if (l.fim > l.inicio && t < l.fim) return this.medidas[i].topo + Math.max(0, (t - l.inicio) / (l.fim - l.inicio)) * this.medidas[i].altura;
    }
    return this.medidas[this.medidas.length - 1].topo;
  }

  private rolarAte(t: number, animar: boolean, fracaoDaTela = 0.4): void {
    window.scrollTo({
      top: Math.max(0, this.posicaoDaData(t) - window.innerHeight * fracaoDaTela),
      behavior: animar && !movimentoReduzido() ? "smooth" : "auto",
    });
  }

  irParaHoje(animar: boolean): void {
    this.rolarAte(this.hoje, animar, 0.3);
  }

  private aoRolar(): void {
    this.agendado = false;
    if (!this.medidas.length) return;
    const alturaDoCabecalho = this.el.cabecalho.offsetHeight;
    const y = window.scrollY;
    const t = this.dataNaPosicao(y + alturaDoCabecalho + 70);
    const futuro = t > this.hoje + 864e5;
    const capitulos = futuro ? [] : capitulosEntre(this.linha.capitulos, t, t + 1);
    this.el.contexto.innerHTML = `<b>${ano(t)} · ${idadeEm(this.nascimento, t)} anos</b>${futuro ? "<span>futuro em aberto</span>" : ""}`
      + capitulos.map((c) => `<span class="chip"><i style="color:${corCss(c.capitulo.cor)}"></i>${esc(c.capitulo.nome)}</span>`).join("");
    const principal = capitulos.filter((c) => c.capitulo.principal).sort((a, b) => a.inicio - b.inicio)[0];
    document.documentElement.style.setProperty("--ambiente", principal ? corCss(principal.capitulo.cor) : "transparent");

    const altura = this.el.canvas.clientHeight;
    const total = this.linha.fim - this.nascimento;
    const t1 = this.dataNaPosicao(y + alturaDoCabecalho);
    const t2 = this.dataNaPosicao(y + window.innerHeight);
    const y1 = ((t1 - this.nascimento) / total) * altura;
    const y2 = ((t2 - this.nascimento) / total) * altura;
    this.el.visor.style.top = `${this.el.canvas.offsetTop + y1}px`;
    this.el.visor.style.height = `${Math.max(8, y2 - y1)}px`;
  }

  // ---------- interações ----------

  private mudarGranularidade(g: Granularidade, ancora?: number): void {
    const t = ancora ?? this.dataNaPosicao(window.scrollY + window.innerHeight * 0.4);
    this.granularidade = g;
    try {
      localStorage.setItem(GUARDAR_GRANULARIDADE, g);
    } catch {
      // sem armazenamento, a escolha vale só nesta visita
    }
    this.desenhar();
    this.rolarAte(t, false);
  }

  private irParaMemoria(id: string): void {
    this.el.dialogo.close();
    let cartao = this.el.lista.querySelector<HTMLElement>(`[data-memoria="${CSS.escape(id)}"]`);
    if (!cartao) {
      const m = this.memoriaPorId.get(id);
      if (!m) return;
      this.mudarGranularidade("mes", lerData(m.data));
      cartao = this.el.lista.querySelector<HTMLElement>(`[data-memoria="${CSS.escape(id)}"]`);
    }
    if (!cartao) return;
    cartao.scrollIntoView({ block: "center", behavior: movimentoReduzido() ? "auto" : "smooth" });
    cartao.classList.remove("piscar");
    void cartao.offsetWidth;
    cartao.classList.add("piscar");
  }

  private abrirMemoria(id: string): void {
    const m = this.memoriaPorId.get(id);
    if (!m) return;
    this.el.conteudoDoDialogo.innerHTML = desenharDetalhe(m, this.contexto(), lerData(m.data));
    this.el.dialogo.showModal();
  }

  private pularPeloMinimapa(evento: PointerEvent): void {
    const caixa = this.el.canvas.getBoundingClientRect();
    const fracao = Math.min(1, Math.max(0, (evento.clientY - caixa.top) / caixa.height));
    this.rolarAte(this.nascimento + fracao * (this.linha.fim - this.nascimento), false, 0.45);
  }

  private ligarEventos(): void {
    window.addEventListener("scroll", () => {
      if (!this.agendado) {
        this.agendado = true;
        requestAnimationFrame(() => this.aoRolar());
      }
    }, { passive: true });

    let espera: number | undefined;
    window.addEventListener("resize", () => {
      clearTimeout(espera);
      espera = window.setTimeout(() => {
        const t = this.dataNaPosicao(window.scrollY + window.innerHeight * 0.4);
        this.medir();
        this.desenharMinimapa();
        this.rolarAte(t, false);
      }, 150);
    });

    for (const b of this.el.botoesDeGranularidade) {
      b.addEventListener("click", () => this.mudarGranularidade(b.dataset.granularidade as Granularidade));
    }
    this.el.botaoHoje.addEventListener("click", () => this.irParaHoje(true));

    this.el.minimapa.addEventListener("pointerdown", (e) => {
      this.el.minimapa.setPointerCapture(e.pointerId);
      this.pularPeloMinimapa(e);
    });
    this.el.minimapa.addEventListener("pointermove", (e) => {
      if (e.buttons) this.pularPeloMinimapa(e);
    });

    document.addEventListener("click", (e) => {
      const alvo = (e.target as HTMLElement).closest<HTMLElement>("[data-ir],[data-memoria],[data-ampliar],[data-fechar]");
      if (!alvo) return;
      if (alvo.dataset.ir) this.irParaMemoria(alvo.dataset.ir);
      else if (alvo.dataset.memoria) this.abrirMemoria(alvo.dataset.memoria);
      else if (alvo.dataset.ampliar) this.mudarGranularidade("mes", Number(alvo.dataset.ampliar));
      else if (alvo.hasAttribute("data-fechar")) this.el.dialogo.close();
    });
    this.el.dialogo.addEventListener("click", (e) => {
      if (e.target === this.el.dialogo) this.el.dialogo.close();
    });

    // as fontes chegam depois do primeiro desenho e mudam as alturas das linhas
    document.fonts?.ready.then(() => {
      const t = this.dataNaPosicao(window.scrollY + window.innerHeight * 0.3);
      this.medir();
      this.rolarAte(t, false, 0.3);
      this.aoRolar();
    });
  }
}
