// Tela "Conta": aparelhos conectados, trocar senha, sair e, para o administrador, convites.

import { api } from "../api";
import { esc } from "../linha-do-tempo/desenho";
import type { Conta, LinkGerado } from "../tipos";

/** Descreve o aparelho a partir do navegador, de forma curta ("Chrome no Android"). */
export function descreverAparelho(agente: string): string {
  const sistema = /Android/.test(agente) ? "Android" : /iPhone|iPad/.test(agente) ? "iPhone" : /Windows/.test(agente) ? "Windows"
    : /Mac OS/.test(agente) ? "Mac" : /Linux/.test(agente) ? "Linux" : "";
  const navegador = /Edg\//.test(agente) ? "Edge" : /Firefox\//.test(agente) ? "Firefox" : /Chrome\//.test(agente) ? "Chrome"
    : /Safari\//.test(agente) ? "Safari" : "";
  if (navegador && sistema) return `${navegador} no ${sistema}`;
  return navegador || sistema || "Aparelho desconhecido";
}

const dataCurta = (iso: string) => new Date(iso).toLocaleDateString("pt-BR", { day: "numeric", month: "short", year: "numeric" });

function blocoDeLink(link: LinkGerado, explicacao: string): string {
  const endereco = location.origin + link.caminho;
  return `<div class="link-gerado">
    <p>${explicacao} Vale até ${dataCurta(link.valido_ate)} e só uma vez. <strong>Ele aparece só agora.</strong></p>
    <input type="text" readonly value="${esc(endereco)}" aria-label="Link" data-link>
    <button type="button" class="botao" data-copiar>Copiar link</button>
  </div>`;
}

export async function abrirConta(dialogo: HTMLDialogElement, conta: Conta, aoSair: () => void): Promise<void> {
  dialogo.innerHTML = `<div class="formulario conta">
    <h2>Conta</h2>
    <p class="email">${esc(conta.email)}${conta.administrador ? ' <span class="selo">administrador</span>' : ""}</p>

    <section><h3>Aparelhos conectados</h3><ul class="aparelhos" data-aparelhos><li>Carregando…</li></ul></section>

    <section><h3>Trocar senha</h3>
      <form class="troca" data-troca novalidate>
        <label class="campo">Senha atual <input type="password" name="atual" autocomplete="current-password" required></label>
        <label class="campo">Senha nova <small>pelo menos 10 caracteres</small><input type="password" name="nova" autocomplete="new-password" required minlength="10"></label>
        <p class="mensagem" data-mensagem-senha hidden></p>
        <button type="submit" class="botao">Trocar senha</button>
      </form>
    </section>

    ${conta.administrador ? `<section><h3>Convidar alguém</h3>
      <p class="explica">Cada pessoa convidada tem a própria conta e só vê o que é dela. Você não vê nada dela pelo aplicativo.</p>
      <button type="button" class="botao" data-convidar>Gerar link de convite</button>
      <div data-convite></div>
      <ul class="convites" data-convites></ul>
    </section>
    <section><h3>Senha esquecida</h3>
      <form class="troca" data-redefinir novalidate>
        <label class="campo">E-mail da pessoa <input type="email" name="email" required></label>
        <button type="submit" class="botao">Gerar link de senha nova</button>
      </form>
      <div data-redefinicao></div>
    </section>` : ""}

    <p class="erro" data-erro role="alert" hidden></p>
    <div class="acoes"><button type="button" class="botao perigo" data-sair>Sair deste aparelho</button><span class="espaco"></span><button type="button" class="botao" data-fechar-conta>Fechar</button></div>
  </div>`;
  dialogo.showModal();

  const $ = <T extends HTMLElement>(s: string) => dialogo.querySelector<T>(s)!;
  const erro = (texto: string | null) => {
    $("[data-erro]").textContent = texto ?? "";
    $("[data-erro]").hidden = !texto;
  };
  const falhou = (f: unknown) => erro(f instanceof Error ? f.message : "Algo deu errado.");

  async function desenharAparelhos() {
    const lista = await api.sessoes();
    $("[data-aparelhos]").innerHTML = lista.map((s) => `<li>
      <span><strong>${esc(descreverAparelho(s.aparelho))}</strong>${s.esta ? ' <span class="selo">este aparelho</span>' : ""}
      <small>desde ${dataCurta(s.criado_em)} · último uso ${dataCurta(s.ultimo_uso)}</small></span>
      ${s.esta ? "" : `<button type="button" class="botao" data-desconectar="${s.id}">Desconectar</button>`}</li>`).join("");
  }

  async function desenharConvites() {
    if (!conta.administrador) return;
    const lista = await api.admin.convites();
    $("[data-convites]").innerHTML = lista.slice(0, 10).map((c) => {
      const vencido = new Date(c.valido_ate) < new Date();
      const situacao = c.usado ? "usado" : c.cancelado ? "cancelado" : vencido ? "vencido" : `vale até ${dataCurta(c.valido_ate)}`;
      const ativo = !c.usado && !c.cancelado && !vencido;
      return `<li><span>Convite de ${dataCurta(c.criado_em)} <small>${situacao}</small></span>
        ${ativo ? `<button type="button" class="botao" data-cancelar-convite="${c.id}">Cancelar</button>` : ""}</li>`;
    }).join("");
  }

  dialogo.onclick = async (e) => {
    if (e.target === dialogo) return dialogo.close();
    const alvo = (e.target as HTMLElement).closest<HTMLElement>("button");
    if (!alvo) return;
    erro(null);
    try {
      if (alvo.hasAttribute("data-fechar-conta")) dialogo.close();
      else if (alvo.hasAttribute("data-sair")) {
        await api.sair();
        dialogo.close();
        aoSair();
      } else if (alvo.dataset.desconectar) {
        await api.desconectar(alvo.dataset.desconectar);
        await desenharAparelhos();
      } else if (alvo.hasAttribute("data-convidar")) {
        $("[data-convite]").innerHTML = blocoDeLink(await api.admin.criarConvite(), "Envie este link para a pessoa.");
        await desenharConvites();
      } else if (alvo.dataset.cancelarConvite) {
        await api.admin.cancelarConvite(alvo.dataset.cancelarConvite);
        await desenharConvites();
      } else if (alvo.hasAttribute("data-copiar")) {
        const campo = alvo.parentElement!.querySelector<HTMLInputElement>("[data-link]")!;
        try {
          await navigator.clipboard.writeText(campo.value);
          alvo.textContent = "Copiado";
        } catch {
          campo.select(); // sem acesso à área de transferência: deixa o texto selecionado para copiar à mão
        }
      }
    } catch (f) {
      falhou(f);
    }
  };

  $<HTMLFormElement>("[data-troca]").addEventListener("submit", async (e) => {
    e.preventDefault();
    const form = e.target as HTMLFormElement;
    const mensagem = $("[data-mensagem-senha]");
    const atual = (form.elements.namedItem("atual") as HTMLInputElement).value;
    const nova = (form.elements.namedItem("nova") as HTMLInputElement).value;
    try {
      if (nova.length < 10) throw new Error("A senha nova precisa de pelo menos 10 caracteres.");
      await api.trocarSenha(atual, nova);
      form.reset();
      mensagem.textContent = "Senha trocada. Os outros aparelhos foram desconectados.";
      mensagem.hidden = false;
      await desenharAparelhos();
    } catch (f) {
      falhou(f);
    }
  });

  if (conta.administrador) {
    $<HTMLFormElement>("[data-redefinir]").addEventListener("submit", async (e) => {
      e.preventDefault();
      const email = ((e.target as HTMLFormElement).elements.namedItem("email") as HTMLInputElement).value;
      try {
        $("[data-redefinicao]").innerHTML = blocoDeLink(await api.admin.criarRedefinicao(email), "Envie este link para a pessoa criar a senha nova.");
      } catch (f) {
        falhou(f);
      }
    });
  }

  await Promise.all([desenharAparelhos(), desenharConvites()]).catch(falhou);
}
