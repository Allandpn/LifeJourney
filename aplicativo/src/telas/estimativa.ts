// Tela "Estimativa": a faixa provável, o "e se?", o histórico e o questionário.
// Fica fora da tela principal de propósito: a linha do tempo só usa a faixa para dar forma ao futuro.

import { api } from "../api";
import { esc } from "../linha-do-tempo/desenho";
import type { EnvioDeRespostas, Estimativa, Pergunta, RodadaDeRespostas } from "../tipos";

const SEMANAS_POR_ANO = 52.1775;
const anos = (x: number) => Math.round(x).toString();
const umaCasa = (x: number) => x.toFixed(1).replace(".", ",");
const semanas = (x: number) => Math.round(x).toLocaleString("pt-BR");
const dataCurta = (iso: string) => new Date(iso).toLocaleDateString("pt-BR", { day: "numeric", month: "short", year: "numeric" });

/** Barra da faixa: sólida até o P10, esmaecendo até o P90, com a mediana marcada. */
function barra(e: Estimativa, idadeAtual: number): string {
  const inicio = idadeAtual;
  const fim = e.p90 + 5;
  const pos = (x: number) => `${(((x - inicio) / (fim - inicio)) * 100).toFixed(2)}%`;
  return `<div class="faixa" role="img" aria-label="Faixa provável dos ${anos(e.p10)} aos ${anos(e.p90)} anos, mediana ${anos(e.mediana)}">
    <span class="faixa-certa" style="width:${pos(e.p10)}"></span>
    <span class="faixa-provavel" style="left:${pos(e.p10)};width:calc(${pos(e.p90)} - ${pos(e.p10)})"></span>
    <span class="faixa-mediana" style="left:${pos(e.mediana)}"></span>
    <span class="faixa-rotulo" style="left:0">hoje · ${anos(idadeAtual)}</span>
    <span class="faixa-rotulo" style="left:${pos(e.p10)}">${anos(e.p10)}</span>
    <span class="faixa-rotulo meio" style="left:${pos(e.mediana)}">${anos(e.mediana)}</span>
    <span class="faixa-rotulo" style="left:${pos(e.p90)}">${anos(e.p90)}</span>
  </div>`;
}

function visaoDoResultado(e: Estimativa, idadeAtual: number, historico: RodadaDeRespostas[]): string {
  const base = e.base === "questionario"
    ? `Com as suas respostas de ${dataCurta(e.respondido_em!)}.`
    : "Sem questionário: é a faixa de uma pessoa brasileira média do seu sexo e idade.";
  const semanasAteMediana = (e.mediana - idadeAtual) * SEMANAS_POR_ANO;
  const individuais = e.e_se.filter((m) => m.fator !== "todas");
  const todas = e.e_se.find((m) => m.fator === "todas");
  const eSe = individuais.length
    ? `<section><h3>E se?</h3>
        <p class="explica">Mudanças nos hábitos que dependem de você, e quantas semanas cada uma acrescenta à média.</p>
        <ul class="e-se">${individuais.map((m) => `<li><span>${esc(m.acao)}</span><strong>+${semanas(m.ganho_semanas)} semanas</strong></li>`).join("")}
        ${todas ? `<li class="todas"><span>Todas juntas</span><strong>+${semanas(todas.ganho_semanas)} semanas</strong></li>` : ""}</ul>
      </section>`
    : e.base === "questionario"
      ? '<section><h3>E se?</h3><p class="explica">Nas suas respostas, os hábitos que o questionário mede já estão na opção mais saudável.</p></section>'
      : "";
  const linhas = historico.slice(0, 8).map((h) =>
    `<li><span>${dataCurta(h.criado_em)}</span><span>faixa ${anos(h.resultado.p10)}–${anos(h.resultado.p90)} · metade passa dos ${anos(h.resultado.mediana)}</span></li>`).join("");

  return `<h2>Estimativa</h2>
    <p class="explica">${base}</p>
    ${barra(e, idadeAtual)}
    <dl class="numeros">
      <div><dt>Faixa provável</dt><dd>dos ${anos(e.p10)} aos ${anos(e.p90)} anos</dd></div>
      <div><dt>Metade das vidas parecidas</dt><dd>passa dos ${anos(e.mediana)} anos</dd></div>
      <div><dt>Até o meio da faixa</dt><dd>cerca de ${semanas(semanasAteMediana)} semanas, todas ainda suas</dd></div>
    </dl>
    ${eSe}
    <div class="linha-de-botoes"><button type="button" class="botao principal" data-questionario>${e.base === "questionario" ? "Atualizar respostas" : "Responder o questionário"}</button></div>
    ${linhas ? `<section><h3>Respostas anteriores</h3><ul class="historico">${linhas}</ul></section>` : ""}
    <p class="ressalva">É uma estimativa estatística, parte da tábua de mortalidade do IBGE ajustada por estudos científicos. Não é aconselhamento médico, e ninguém tem data marcada. Os números ainda são provisórios: as médias brasileiras e a calibração do modelo estão sendo conferidas. Risco relativo atual: ${umaCasa(e.hr_total)}.</p>
    ${historico.length ? '<button type="button" class="botao perigo" data-apagar-respostas>Apagar minhas respostas de saúde</button>' : ""}
    <div class="acoes"><span class="espaco"></span><button type="button" class="botao" data-fechar-estimativa>Fechar</button></div>`;
}

function visaoDoQuestionario(perguntas: Pergunta[], anterior: RodadaDeRespostas | undefined): string {
  const r = anterior?.respostas ?? {};
  const itens = perguntas.map((p) => {
    if (p.tipo === "altura_e_peso") {
      return `<fieldset class="campo pergunta"><legend>${esc(p.pergunta)}</legend>
        <div class="dois">
          <label class="campo">Altura (cm) <input type="number" name="altura" inputmode="numeric" min="100" max="250" value="${anterior?.altura_m ? Math.round(anterior.altura_m * 100) : ""}"></label>
          <label class="campo">Peso (kg) <input type="number" name="peso" inputmode="decimal" min="25" max="350" step="0.1" value="${anterior?.peso_kg ?? ""}"></label>
        </div>
        <small class="fonte">Deixe em branco para pular. Fonte: ${esc(p.fonte)}</small></fieldset>`;
    }
    const opcoes = [{ valor: "", rotulo: "prefiro não responder" }, ...p.opcoes];
    return `<fieldset class="campo pergunta"><legend>${esc(p.pergunta)}</legend>
      <div class="opcoes fichas" role="radiogroup">${opcoes.map((o) =>
        `<label><input type="radio" name="${p.fator}" value="${o.valor}"${(r[p.fator] ?? "") === o.valor ? " checked" : ""}><span>${esc(o.rotulo)}</span></label>`).join("")}</div>
      <small class="fonte">Fonte: ${esc(p.fonte)}</small></fieldset>`;
  }).join("");
  return `<h2>Questionário</h2>
    <p class="explica">Perguntas curtas, cada uma ligada a um estudo publicado. Pule o que quiser: pergunta pulada conta como a média brasileira. As respostas ficam só na sua conta, e você pode apagá-las quando quiser.</p>
    <form class="questionario" novalidate>${itens}
      <p class="erro" data-erro role="alert" hidden></p>
      <div class="acoes"><button type="button" class="botao" data-voltar>Voltar</button><span class="espaco"></span><button type="submit" class="botao principal">Ver minha faixa</button></div>
    </form>`;
}

function lerEnvio(form: HTMLFormElement, perguntas: Pergunta[]): EnvioDeRespostas {
  const respostas: Record<string, string> = {};
  for (const p of perguntas) {
    if (p.tipo !== "opcoes") continue;
    const valor = form.querySelector<HTMLInputElement>(`input[name="${p.fator}"]:checked`)?.value;
    if (valor) respostas[p.fator] = valor;
  }
  const altura = (form.elements.namedItem("altura") as HTMLInputElement | null)?.value;
  const peso = (form.elements.namedItem("peso") as HTMLInputElement | null)?.value?.replace(",", ".");
  if (!!altura !== !!peso) throw new Error("Para o IMC, preencha a altura e o peso, ou deixe os dois em branco.");
  return { respostas, altura_m: altura ? Number(altura) / 100 : null, peso_kg: peso ? Number(peso) : null };
}

/** Abre a tela. `aoMudar` é chamado quando a faixa muda (para a linha do tempo redesenhar o futuro). */
export async function abrirEstimativa(dialogo: HTMLDialogElement, nascimento: string, aoMudar: () => void): Promise<void> {
  const idadeAtual = (Date.now() - new Date(`${nascimento}T00:00:00`).getTime()) / (365.2425 * 864e5);
  dialogo.innerHTML = '<div class="formulario estimativa"><p class="explica">Carregando…</p></div>';
  if (!dialogo.open) dialogo.showModal();
  const caixa = dialogo.querySelector<HTMLElement>(".estimativa")!;
  let armadoParaApagar = false;

  const mostrarResultado = async (estimativa?: Estimativa) => {
    const [e, historico] = await Promise.all([estimativa ? Promise.resolve(estimativa) : api.estimativa(), api.questionario.historico()]);
    caixa.innerHTML = visaoDoResultado(e, idadeAtual, historico);
    caixa.scrollTop = 0;
    dialogo.scrollTop = 0;
  };

  const mostrarQuestionario = async () => {
    const [perguntas, historico] = await Promise.all([api.questionario.perguntas(), api.questionario.historico()]);
    caixa.innerHTML = visaoDoQuestionario(perguntas, historico[0]);
    dialogo.scrollTop = 0;
    const form = caixa.querySelector<HTMLFormElement>("form")!;
    const erro = form.querySelector<HTMLElement>("[data-erro]")!;
    form.addEventListener("input", () => { erro.hidden = true; });
    form.addEventListener("submit", async (ev) => {
      ev.preventDefault();
      const botao = form.querySelector<HTMLButtonElement>("button[type=submit]")!;
      botao.disabled = true;
      try {
        const nova = await api.questionario.responder(lerEnvio(form, perguntas));
        aoMudar();
        await mostrarResultado(nova);
      } catch (falha) {
        erro.textContent = falha instanceof Error ? falha.message : "Não foi possível salvar.";
        erro.hidden = false;
        botao.disabled = false;
      }
    });
  };

  dialogo.onclick = async (ev) => {
    if (ev.target === dialogo) return dialogo.close();
    const alvo = (ev.target as HTMLElement).closest<HTMLElement>("button");
    if (!alvo) return;
    if (alvo.hasAttribute("data-fechar-estimativa")) dialogo.close();
    else if (alvo.hasAttribute("data-questionario")) await mostrarQuestionario();
    else if (alvo.hasAttribute("data-voltar")) await mostrarResultado();
    else if (alvo.hasAttribute("data-apagar-respostas")) {
      if (!armadoParaApagar) {
        armadoParaApagar = true;
        alvo.textContent = "Toque de novo para apagar todas as respostas";
        alvo.classList.add("armado");
        return;
      }
      await api.questionario.apagar();
      armadoParaApagar = false;
      aoMudar();
      await mostrarResultado();
    }
  };

  await mostrarResultado();
}
