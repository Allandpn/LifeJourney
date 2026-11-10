// Telas de quem ainda não entrou: entrar, criar conta por convite e criar senha nova.

import { api } from "../api";

const MINIMO = 10;

function tela(el: HTMLElement, html: string): HTMLFormElement {
  el.hidden = false;
  el.innerHTML = `<form class="boas-vindas acesso" novalidate>${html}<p class="erro" data-erro role="alert" hidden></p></form>`;
  return el.querySelector("form")!;
}

function titulo(etiqueta: string): string {
  return `<span class="etiqueta">${etiqueta}</span><h1>Vida em <span>Semanas</span></h1>`;
}

function enviar(form: HTMLFormElement, rotulo: string, acao: () => Promise<void>): void {
  const erro = form.querySelector<HTMLElement>("[data-erro]")!;
  const botao = form.querySelector<HTMLButtonElement>("button[type=submit]")!;
  form.addEventListener("input", () => { erro.hidden = true; });
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    botao.disabled = true;
    botao.textContent = "Aguarde…";
    try {
      await acao();
    } catch (falha) {
      erro.textContent = falha instanceof Error ? falha.message : "Algo deu errado.";
      erro.hidden = false;
      botao.disabled = false;
      botao.textContent = rotulo;
    }
  });
}

const campo = (form: HTMLFormElement, nome: string) => (form.elements.namedItem(nome) as HTMLInputElement).value;

function conferirSenhas(form: HTMLFormElement): string {
  const senha = campo(form, "senha");
  if (senha.length < MINIMO) throw new Error(`A senha precisa de pelo menos ${MINIMO} caracteres.`);
  if (senha !== campo(form, "repetir")) throw new Error("As duas senhas não são iguais.");
  return senha;
}

const camposDeSenhaNova = `
  <label>Senha <small>pelo menos ${MINIMO} caracteres; uma frase curta funciona bem</small>
    <input type="password" name="senha" autocomplete="new-password" required minlength="${MINIMO}"></label>
  <label>Repita a senha <input type="password" name="repetir" autocomplete="new-password" required></label>`;

export function telaDeEntrar(el: HTMLElement, aoEntrar: () => void): void {
  const form = tela(el, `${titulo("Entrar")}
    <label>E-mail <input type="email" name="email" autocomplete="username" required></label>
    <label>Senha <input type="password" name="senha" autocomplete="current-password" required></label>
    <button type="submit" class="botao principal">Entrar</button>
    <p class="ajuda">Esqueceu a senha? Peça ao administrador do servidor um link para criar outra.</p>`);
  (form.elements.namedItem("email") as HTMLInputElement).focus();
  enviar(form, "Entrar", async () => {
    await api.entrar(campo(form, "email"), campo(form, "senha"));
    el.hidden = true;
    aoEntrar();
  });
}

export function telaDeCriarConta(el: HTMLElement, codigo: string, aoCriar: () => void): void {
  const form = tela(el, `${titulo("Convite")}
    <p>Você recebeu um convite para criar uma conta. Ela é só sua: ninguém vê as suas memórias pelo aplicativo.</p>
    <p class="aviso-servidor">Os dados ficam num servidor caseiro, cuidado por quem te convidou. Essa pessoa não vê nada pelo aplicativo, mas, como tem acesso ao aparelho, tecnicamente poderia abrir o arquivo do banco. Por isso, registre aqui só o que você se sente bem guardando.</p>
    <label>E-mail <input type="email" name="email" autocomplete="username" required></label>
    ${camposDeSenhaNova}
    <button type="submit" class="botao principal">Criar conta</button>`);
  enviar(form, "Criar conta", async () => {
    const senha = conferirSenhas(form);
    await api.criarConta(codigo, campo(form, "email"), senha);
    el.hidden = true;
    aoCriar();
  });
}

export function telaDeRedefinir(el: HTMLElement, codigo: string, aoTerminar: () => void): void {
  const form = tela(el, `${titulo("Senha nova")}
    <p>Escolha uma senha nova. Todos os aparelhos conectados à sua conta vão precisar entrar de novo.</p>
    ${camposDeSenhaNova}
    <button type="submit" class="botao principal">Salvar senha</button>`);
  enviar(form, "Salvar senha", async () => {
    await api.redefinirSenha(codigo, conferirSenhas(form));
    el.hidden = true;
    aoTerminar();
  });
}
