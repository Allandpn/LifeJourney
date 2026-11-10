// Formulários de criar e editar memória, capítulo e intenção.
// Todos usam o mesmo <dialog>; cada função preenche o conteúdo e cuida do envio.

import { api } from "../api";
import { esc } from "../linha-do-tempo/desenho";
import type { Capitulo, CorCapitulo, Emocao, Horizonte, Intencao, Memoria, StatusIntencao } from "../tipos";
import { formatarData, lerData } from "../tempo";

export const LIMITE_TEXTO = 280;
const EMOCOES: Emocao[] = ["alegria", "calma", "orgulho", "saudade", "tristeza", "incerteza"];
const CORES: CorCapitulo[] = ["menta", "azul", "ambar", "laranja", "rosa", "lavanda", "coral"];
const NOMES_DAS_CORES: Record<CorCapitulo, string> = {
  menta: "menta", azul: "azul", ambar: "âmbar", laranja: "laranja", rosa: "rosa", lavanda: "lavanda", coral: "coral",
};
const STATUS: [StatusIntencao, string][] = [
  ["ativa", "ativa"], ["pausada", "pausada"], ["virou_memoria", "virou memória"], ["deixada_de_lado", "deixada de lado"],
];
const CATEGORIAS = ["trabalho", "estudo", "relacionamento", "família", "saúde", "moradia", "transição"];
const LIGACOES_VISIVEIS = 6;

type AoSalvar = (foco?: { memoria?: string; data?: string }) => void;

/** Data de hoje no formato da API ("AAAA-MM-DD"), no fuso local. */
export function hojeIso(): string {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
}

export function instanteParaIso(instante: number): string {
  const d = new Date(instante);
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
}

// ---------- peças comuns ----------

function dialogo(): HTMLDialogElement {
  return document.querySelector<HTMLDialogElement>("#formulario")!;
}

function abrir(html: string): HTMLFormElement {
  const d = dialogo();
  d.innerHTML = `<form class="formulario" novalidate>${html}</form>`;
  d.showModal();
  const form = d.querySelector("form")!;
  form.addEventListener("input", () => mostrarErro(form, null)); // o aviso some quando a pessoa corrige
  form.querySelector<HTMLElement>("[data-cancelar]")?.addEventListener("click", () => d.close());
  return form;
}

function rodape(podeExcluir: boolean): string {
  return `<p class="erro" data-erro role="alert" hidden></p>
    <div class="acoes">
      ${podeExcluir ? '<button type="button" class="botao perigo" data-excluir>Excluir</button>' : ""}
      <span class="espaco"></span>
      <button type="button" class="botao" data-cancelar>Cancelar</button>
      <button type="submit" class="botao principal" data-salvar>Salvar</button>
    </div>`;
}

function mostrarErro(form: HTMLFormElement, mensagem: string | null): void {
  const el = form.querySelector<HTMLElement>("[data-erro]")!;
  el.textContent = mensagem ?? "";
  el.hidden = !mensagem;
}

/** Envia o formulário: trava o botão, mostra erros e fecha ao terminar. */
function aoEnviar(form: HTMLFormElement, acao: () => Promise<void>): void {
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const botao = form.querySelector<HTMLButtonElement>("[data-salvar]")!;
    botao.disabled = true;
    botao.textContent = "Salvando…";
    mostrarErro(form, null);
    try {
      await acao();
      dialogo().close();
    } catch (erro) {
      mostrarErro(form, erro instanceof Error ? erro.message : "Não foi possível salvar.");
      botao.disabled = false;
      botao.textContent = "Salvar";
    }
  });
}

/** Excluir pede um segundo toque, sem janela de confirmação. */
function aoExcluir(form: HTMLFormElement, acao: () => Promise<void>): void {
  const botao = form.querySelector<HTMLButtonElement>("[data-excluir]");
  if (!botao) return;
  let armado = false;
  let espera: number | undefined;
  botao.addEventListener("click", async () => {
    if (!armado) {
      armado = true;
      botao.textContent = "Toque de novo para excluir";
      botao.classList.add("armado");
      espera = window.setTimeout(() => {
        armado = false;
        botao.textContent = "Excluir";
        botao.classList.remove("armado");
      }, 4000);
      return;
    }
    clearTimeout(espera);
    botao.disabled = true;
    try {
      await acao();
      dialogo().close();
    } catch (erro) {
      mostrarErro(form, erro instanceof Error ? erro.message : "Não foi possível excluir.");
      botao.disabled = false;
    }
  });
}

const valor = (form: HTMLFormElement, nome: string) =>
  (form.elements.namedItem(nome) as HTMLInputElement | HTMLTextAreaElement | null)?.value.trim() ?? "";
const marcado = (form: HTMLFormElement, nome: string) =>
  (form.elements.namedItem(nome) as HTMLInputElement).checked;
const escolhido = (form: HTMLFormElement, nome: string) =>
  form.querySelector<HTMLInputElement>(`input[name="${nome}"]:checked`)?.value ?? "";

function opcoes(nome: string, lista: [string, string][], atual: string, classe = "opcoes"): string {
  return `<div class="${classe}" role="radiogroup">${lista
    .map(([v, rotulo]) => `<label><input type="radio" name="${nome}" value="${v}"${v === atual ? " checked" : ""}><span>${rotulo}</span></label>`)
    .join("")}</div>`;
}

// ---------- memória ----------

export interface OpcoesDeMemoria {
  memoria?: Memoria;
  data?: string; // data sugerida para uma memória nova
  nascimento: string;
  todas: Memoria[];
  aoSalvar: AoSalvar;
}

export function formularioDeMemoria(o: OpcoesDeMemoria): void {
  const m = o.memoria;
  const hoje = hojeIso();
  const data = m?.data ?? (o.data && o.data < hoje ? o.data : hoje);
  let fotoNova: File | null = null;
  let removerFoto = false;
  const ligadas = new Set(m?.veio_de ?? []);

  const form = abrir(`
    <h2>${m ? "Editar memória" : "Nova memória"}</h2>
    <label class="campo">O que aconteceu?
      <textarea name="texto" maxlength="${LIMITE_TEXTO}" rows="4" required placeholder="Uma ou duas frases bastam.">${esc(m?.texto ?? "")}</textarea>
      <span class="contador" data-contador></span>
    </label>
    <label class="campo">Quando <input type="date" name="data" required value="${data}" min="${o.nascimento}" max="${hoje}"></label>
    <div class="campo foto-campo">
      <span>Foto</span>
      <div class="foto-previa" data-previa ${m?.foto ? `style="background-image:url('${m.foto}')"` : "hidden"}></div>
      <div class="linha-de-botoes">
        <label class="botao"><input type="file" accept="image/*" data-arquivo hidden>${m?.foto ? "Trocar foto" : "Escolher foto"}</label>
        <button type="button" class="botao" data-sem-foto ${m?.foto ? "" : "hidden"}>Remover foto</button>
      </div>
    </div>
    <fieldset class="campo"><legend>Como foi</legend>
      ${opcoes("emocao", [["", "sem nome"], ...EMOCOES.map((e) => [e, e] as [string, string])], m?.emocao ?? "", "opcoes fichas")}
    </fieldset>
    <fieldset class="campo"><legend>Intensidade</legend>
      ${opcoes("intensidade", [["1", "leve"], ["2", "média"], ["3", "forte"]], String(m?.intensidade ?? 2), "opcoes segmentos")}
    </fieldset>
    <label class="interruptor"><input type="checkbox" name="marcante"${m?.marcante ? " checked" : ""}><span>Marcante <small>aparece primeiro no nível Ano</small></span></label>
    <label class="interruptor"><input type="checkbox" name="silenciar"${m?.silenciar ? " checked" : ""}><span>Não me lembrar disto <small>fica fora de “nesta semana, em outros anos”</small></span></label>
    <fieldset class="campo ligacoes-campo"><legend>Veio de <small>outra memória que levou a esta</small></legend>
      <div class="escolhidas" data-escolhidas></div>
      <input type="search" placeholder="Buscar memória" data-busca aria-label="Buscar memória para ligar">
      <div class="candidatas" data-candidatas></div>
    </fieldset>
    ${rodape(!!m)}`);

  // contador de caracteres
  const texto = form.elements.namedItem("texto") as HTMLTextAreaElement;
  const contador = form.querySelector<HTMLElement>("[data-contador]")!;
  const contar = () => {
    const resta = LIMITE_TEXTO - texto.value.length;
    contador.textContent = `${resta}`;
    contador.classList.toggle("pouco", resta < 30);
  };
  texto.addEventListener("input", contar);
  contar();

  // foto
  const previa = form.querySelector<HTMLElement>("[data-previa]")!;
  const semFoto = form.querySelector<HTMLButtonElement>("[data-sem-foto]")!;
  form.querySelector<HTMLInputElement>("[data-arquivo]")!.addEventListener("change", (e) => {
    const arquivo = (e.target as HTMLInputElement).files?.[0];
    if (!arquivo) return;
    fotoNova = arquivo;
    removerFoto = false;
    previa.style.backgroundImage = `url('${URL.createObjectURL(arquivo)}')`;
    previa.hidden = false;
    semFoto.hidden = false;
  });
  semFoto.addEventListener("click", () => {
    fotoNova = null;
    removerFoto = !!m?.foto;
    previa.hidden = true;
    previa.style.backgroundImage = "";
    semFoto.hidden = true;
  });

  // ligações "veio de": só memórias anteriores (ou do mesmo dia), menos a própria
  const escolhidas = form.querySelector<HTMLElement>("[data-escolhidas]")!;
  const candidatas = form.querySelector<HTMLElement>("[data-candidatas]")!;
  const busca = form.querySelector<HTMLInputElement>("[data-busca]")!;
  const porId = new Map(o.todas.map((x) => [x.id, x]));
  const desenharLigacoes = () => {
    const dataAtual = valor(form, "data") || hoje;
    escolhidas.innerHTML = [...ligadas].map((id) => {
      const x = porId.get(id);
      return x ? `<button type="button" class="ficha ligada" data-desligar="${id}">${esc(x.texto.slice(0, 40))}${x.texto.length > 40 ? "…" : ""} ✕</button>` : "";
    }).join("");
    const termo = busca.value.trim().toLowerCase();
    const lista = o.todas
      .filter((x) => x.id !== m?.id && !ligadas.has(x.id) && x.data <= dataAtual)
      .filter((x) => !termo || x.texto.toLowerCase().includes(termo))
      .sort((a, b) => b.data.localeCompare(a.data))
      .slice(0, LIGACOES_VISIVEIS);
    candidatas.innerHTML = lista.length
      ? lista.map((x) => `<button type="button" class="candidata" data-ligar="${x.id}"><span>${formatarData(lerData(x.data))}</span>${esc(x.texto)}</button>`).join("")
      : `<p class="sem-resultado">${termo ? "Nenhuma memória encontrada." : "Nenhuma memória anterior ainda."}</p>`;
  };
  form.addEventListener("click", (e) => {
    const alvo = (e.target as HTMLElement).closest<HTMLElement>("[data-ligar],[data-desligar]");
    if (!alvo) return;
    if (alvo.dataset.ligar) {
      ligadas.add(alvo.dataset.ligar);
      busca.value = "";
    }
    if (alvo.dataset.desligar) ligadas.delete(alvo.dataset.desligar);
    desenharLigacoes();
  });
  busca.addEventListener("input", desenharLigacoes);
  (form.elements.namedItem("data") as HTMLInputElement).addEventListener("change", desenharLigacoes);
  desenharLigacoes();

  aoEnviar(form, async () => {
    if (!valor(form, "texto")) throw new Error("Escreva o que aconteceu.");
    if (!valor(form, "data")) throw new Error("Escolha a data.");
    const dados = {
      texto: valor(form, "texto"),
      data: valor(form, "data"),
      emocao: (escolhido(form, "emocao") || null) as Emocao | null,
      intensidade: Number(escolhido(form, "intensidade")) as 1 | 2 | 3,
      marcante: marcado(form, "marcante"),
      silenciar: marcado(form, "silenciar"),
      veio_de: [...ligadas],
    };
    const salva = m ? await api.memorias.alterar(m.id, dados) : await api.memorias.criar(dados);
    if (fotoNova) await api.memorias.enviarFoto(salva.id, fotoNova);
    else if (removerFoto) await api.memorias.removerFoto(salva.id);
    o.aoSalvar({ memoria: salva.id });
  });
  if (m) aoExcluir(form, async () => {
    await api.memorias.excluir(m.id);
    o.aoSalvar({ data: m.data });
  });
  if (!m) texto.focus();
}

// ---------- capítulo ----------

export interface OpcoesDeCapitulo {
  capitulo?: Capitulo;
  inicio?: string;
  nascimento: string;
  aoSalvar: AoSalvar;
}

export function formularioDeCapitulo(o: OpcoesDeCapitulo): void {
  const c = o.capitulo;
  const andamento = c ? c.fim === null : true;
  const form = abrir(`
    <h2>${c ? "Editar capítulo" : "Novo capítulo"}</h2>
    <label class="campo">Nome <input type="text" name="nome" maxlength="120" required value="${esc(c?.nome ?? "")}" placeholder="Ex.: Faculdade, Morando em Lisboa"></label>
    <label class="campo">Começou em <input type="date" name="inicio" required value="${c?.inicio ?? o.inicio ?? ""}" min="${o.nascimento}"></label>
    <label class="interruptor"><input type="checkbox" name="andamento"${andamento ? " checked" : ""}><span>Ainda está em andamento</span></label>
    <label class="campo" data-fim ${andamento ? "hidden" : ""}>Terminou em <input type="date" name="fim" value="${c?.fim ?? ""}" min="${o.nascimento}"></label>
    <fieldset class="campo"><legend>Cor</legend>
      <div class="cores" role="radiogroup">${CORES.map((cor) => `<label title="${NOMES_DAS_CORES[cor]}"><input type="radio" name="cor" value="${cor}"${cor === (c?.cor ?? "azul") ? " checked" : ""}><span style="--cor:var(--cap-${cor})"></span><small>${NOMES_DAS_CORES[cor]}</small></label>`).join("")}</div>
    </fieldset>
    <label class="interruptor"><input type="checkbox" name="principal"${c?.principal ?? true ? " checked" : ""}><span>Capítulo principal <small>define a cor da época; os outros aparecem como fios paralelos</small></span></label>
    <label class="campo">Categoria <small>opcional</small>
      <input type="text" name="categoria" maxlength="120" list="categorias" value="${esc(c?.categoria ?? "")}">
      <datalist id="categorias">${CATEGORIAS.map((x) => `<option value="${x}">`).join("")}</datalist>
    </label>
    <label class="campo">Notas <small>opcional</small><textarea name="notas" rows="3" maxlength="5000">${esc(c?.notas ?? "")}</textarea></label>
    ${rodape(!!c)}`);

  const caixaFim = form.querySelector<HTMLElement>("[data-fim]")!;
  (form.elements.namedItem("andamento") as HTMLInputElement).addEventListener("change", () => {
    caixaFim.hidden = marcado(form, "andamento");
  });

  aoEnviar(form, async () => {
    if (!valor(form, "nome")) throw new Error("Dê um nome ao capítulo.");
    if (!valor(form, "inicio")) throw new Error("Escolha quando o capítulo começou.");
    const fim = marcado(form, "andamento") ? null : valor(form, "fim") || null;
    if (!marcado(form, "andamento") && !fim) throw new Error("Escolha quando o capítulo terminou, ou marque que está em andamento.");
    const dados = {
      nome: valor(form, "nome"),
      inicio: valor(form, "inicio"),
      fim,
      cor: escolhido(form, "cor") as CorCapitulo,
      principal: marcado(form, "principal"),
      categoria: valor(form, "categoria") || null,
      notas: valor(form, "notas") || null,
    };
    const salvo = c ? await api.capitulos.alterar(c.id, dados) : await api.capitulos.criar(dados);
    o.aoSalvar({ data: salvo.inicio });
  });
  if (c) aoExcluir(form, async () => {
    await api.capitulos.excluir(c.id);
    o.aoSalvar({ data: c.inicio });
  });
}

// ---------- intenção ----------

/** "2027-04" (campo de mês) <-> "2027-04-01" (data da API). */
const mesParaData = (mes: string) => (/^\d{4}-\d{2}$/.test(mes) ? `${mes}-01` : mes);
const dataParaMes = (data: string | undefined) => data?.slice(0, 7) ?? "";

export interface OpcoesDeIntencao {
  intencao?: Intencao;
  aoSalvar: AoSalvar;
}

export function formularioDeIntencao(o: OpcoesDeIntencao): void {
  const i = o.intencao;
  const h = i?.horizonte ?? { tipo: "algum_dia" };
  const mesAtual = hojeIso().slice(0, 7);
  const form = abrir(`
    <h2>${i ? "Editar intenção" : "Nova intenção"}</h2>
    <label class="campo">O que você quer viver? <input type="text" name="nome" maxlength="120" required value="${esc(i?.nome ?? "")}" placeholder="Ex.: Aprender violoncelo"></label>
    <fieldset class="campo"><legend>Quando <small>sem pressa: pode ser vago</small></legend>
      ${opcoes("tipo", [["data", "num mês"], ["intervalo", "num intervalo"], ["algum_dia", "algum dia"]], h.tipo, "opcoes segmentos")}
    </fieldset>
    <label class="campo" data-tipo="data">Mês <input type="month" name="mes" min="${mesAtual}" placeholder="AAAA-MM" value="${dataParaMes(h.tipo === "data" ? h.data : undefined)}"></label>
    <div class="dois" data-tipo="intervalo">
      <label class="campo">De <input type="month" name="de" placeholder="AAAA-MM" value="${dataParaMes(h.tipo === "intervalo" ? h.de : undefined)}"></label>
      <label class="campo">Até <input type="month" name="ate" placeholder="AAAA-MM" value="${dataParaMes(h.tipo === "intervalo" ? h.ate : undefined)}"></label>
    </div>
    ${i ? `<fieldset class="campo"><legend>Situação</legend>${opcoes("status", STATUS, i.status, "opcoes fichas")}</fieldset>` : ""}
    <label class="campo">Notas <small>opcional</small><textarea name="notas" rows="3" maxlength="5000">${esc(i?.notas ?? "")}</textarea></label>
    ${rodape(!!i)}`);

  const mostrarTipo = () => {
    const tipo = escolhido(form, "tipo");
    form.querySelectorAll<HTMLElement>("[data-tipo]").forEach((el) => { el.hidden = el.dataset.tipo !== tipo; });
  };
  form.querySelectorAll('input[name="tipo"]').forEach((el) => el.addEventListener("change", mostrarTipo));
  mostrarTipo();

  aoEnviar(form, async () => {
    if (!valor(form, "nome")) throw new Error("Escreva a intenção.");
    const tipo = escolhido(form, "tipo");
    let horizonte: Horizonte;
    if (tipo === "data") {
      if (!valor(form, "mes")) throw new Error("Escolha o mês, ou marque “algum dia”.");
      horizonte = { tipo: "data", data: mesParaData(valor(form, "mes")) };
    } else if (tipo === "intervalo") {
      if (!valor(form, "de") || !valor(form, "ate")) throw new Error("Escolha o começo e o fim do intervalo.");
      horizonte = { tipo: "intervalo", de: mesParaData(valor(form, "de")), ate: mesParaData(valor(form, "ate")) };
    } else {
      horizonte = { tipo: "algum_dia" };
    }
    const dados = {
      nome: valor(form, "nome"),
      horizonte,
      status: (i ? escolhido(form, "status") : "ativa") as StatusIntencao,
      notas: valor(form, "notas") || null,
      memoria_id: i?.memoria_id ?? null,
    };
    if (i) await api.intencoes.alterar(i.id, dados);
    else await api.intencoes.criar(dados);
    o.aoSalvar({ data: horizonte.tipo === "data" ? horizonte.data : horizonte.tipo === "intervalo" ? horizonte.de : undefined });
  });
  if (i) aoExcluir(form, async () => {
    await api.intencoes.excluir(i.id);
    o.aoSalvar();
  });
}
