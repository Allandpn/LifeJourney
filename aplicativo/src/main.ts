import "./estilo/base.css";
import "./estilo/linha-do-tempo.css";
import "./estilo/formularios.css";
import { api, ErroDaApi, quandoPerderSessao } from "./api";
import { type Dados, TelaDaLinhaDoTempo } from "./linha-do-tempo/tela";
import { telaDeCriarConta, telaDeEntrar, telaDeRedefinir } from "./telas/acesso";
import { mostrarBoasVindas } from "./telas/boas-vindas";
import { abrirConta } from "./telas/conta";
import type { Conta } from "./tipos";
import { formularioDeCapitulo, formularioDeIntencao, formularioDeMemoria, hojeIso } from "./telas/formularios";

const $ = <T extends HTMLElement>(seletor: string) => document.querySelector<T>(seletor)!;

let tela: TelaDaLinhaDoTempo | null = null;
let conta: Conta | null = null;
let dados: Dados | null = null;

function mostrarAviso(texto: string): void {
  const aviso = $("#aviso");
  aviso.textContent = texto;
  aviso.hidden = false;
}

async function carregar(nascimento: string): Promise<Dados> {
  const [memorias, capitulos, intencoes, estimativa] = await Promise.all([
    api.memorias.listar(), api.capitulos.listar(), api.intencoes.listar(), api.estimativa(),
  ]);
  return { nascimento, memorias, capitulos, intencoes, estimativa };
}

/** Depois de salvar: busca tudo de novo e redesenha, indo para o que mudou. */
async function recarregar(foco?: { memoria?: string; data?: string }): Promise<void> {
  if (!dados || !tela) return;
  try {
    dados = await carregar(dados.nascimento);
    tela.atualizar(dados, foco);
  } catch (erro) {
    tratarErro(erro);
  }
}

const pedidos = {
  novaMemoria: (data?: string) =>
    formularioDeMemoria({ data, nascimento: dados!.nascimento, todas: dados!.memorias, aoSalvar: recarregar }),
  editarMemoria: (id: string) => {
    const memoria = dados!.memorias.find((m) => m.id === id);
    if (memoria) formularioDeMemoria({ memoria, nascimento: dados!.nascimento, todas: dados!.memorias, aoSalvar: recarregar });
  },
  novoCapitulo: () => formularioDeCapitulo({ inicio: hojeIso(), nascimento: dados!.nascimento, aoSalvar: recarregar }),
  editarCapitulo: (id: string) => {
    const capitulo = dados!.capitulos.find((c) => c.id === id);
    if (capitulo) formularioDeCapitulo({ capitulo, nascimento: dados!.nascimento, aoSalvar: recarregar });
  },
  novaIntencao: () => formularioDeIntencao({ aoSalvar: recarregar }),
  editarIntencao: (id: string) => {
    const intencao = dados!.intencoes.find((i) => i.id === id);
    if (intencao) formularioDeIntencao({ intencao, aoSalvar: recarregar });
  },
};

function ligarMenuDeCriar(): void {
  const botao = $<HTMLButtonElement>("#botao-criar");
  const menu = $("#menu-criar");
  const fechar = () => {
    menu.hidden = true;
    botao.setAttribute("aria-expanded", "false");
  };
  botao.addEventListener("click", (e) => {
    e.stopPropagation();
    menu.hidden = !menu.hidden;
    botao.setAttribute("aria-expanded", String(!menu.hidden));
  });
  menu.addEventListener("click", (e) => {
    const opcao = (e.target as HTMLElement).closest<HTMLElement>("[data-criar]")?.dataset.criar;
    fechar();
    if (opcao === "memoria") pedidos.novaMemoria();
    if (opcao === "capitulo") pedidos.novoCapitulo();
    if (opcao === "intencao") pedidos.novaIntencao();
  });
  document.addEventListener("click", fechar);
  document.addEventListener("keydown", (e) => e.key === "Escape" && fechar());
}

/** Volta ao começo (tela de entrar), sem o link de convite ou de senha no endereço. */
function recomecar(): void {
  history.replaceState(null, "", location.pathname);
  location.reload();
}

async function iniciar(): Promise<void> {
  // links de convite e de senha nova chegam como "#convite-<código>" e "#redefinir-<código>"
  const [, tipo, codigo] = location.hash.match(/^#(convite|redefinir)-(.+)$/) ?? [];
  const acesso = $("#acesso");
  if (tipo) {
    document.body.dataset.tela = "acesso";
    history.replaceState(null, "", location.pathname); // o código não fica no histórico do navegador
    if (tipo === "convite") telaDeCriarConta(acesso, codigo, () => void iniciar().catch(tratarErro));
    else telaDeRedefinir(acesso, codigo, () => telaDeEntrar(acesso, () => void iniciar().catch(tratarErro)));
    return;
  }
  try {
    conta = await api.conta();
  } catch (erro) {
    if (erro instanceof ErroDaApi && erro.status === 401) {
      document.body.dataset.tela = "acesso";
      telaDeEntrar(acesso, () => void iniciar().catch(tratarErro));
      return;
    }
    throw erro;
  }
  $("#botao-conta").textContent = conta.email.slice(0, 1).toUpperCase();

  const perfil = await api.perfil();
  if (!perfil.nascimento || !perfil.sexo) {
    document.body.dataset.tela = "boas-vindas";
    mostrarBoasVindas($("#boas-vindas"), () => void iniciar().catch(tratarErro));
    return;
  }
  dados = await carregar(perfil.nascimento);
  document.body.dataset.tela = "linha";
  tela = new TelaDaLinhaDoTempo(
    {
      lista: $("#linha"),
      contexto: $("#contexto"),
      cabecalho: $("#cabecalho"),
      minimapa: $("#minimapa"),
      canvas: $<HTMLCanvasElement>("#minimapa canvas"),
      visor: $("#minimapa .visor"),
      dialogo: $<HTMLDialogElement>("#detalhe"),
      conteudoDoDialogo: $("#detalhe .conteudo"),
      botoesDeGranularidade: Array.from(document.querySelectorAll<HTMLButtonElement>("[data-granularidade]")),
      botaoHoje: $<HTMLButtonElement>("#botao-hoje"),
    },
    dados,
    pedidos,
  );
  tela.iniciar();
}

function tratarErro(erro: unknown): void {
  if (erro instanceof ErroDaApi && erro.status === 401) {
    recomecar(); // a sessão acabou (saiu em outro aparelho, trocou a senha): volta para entrar
  } else if (erro instanceof ErroDaApi && erro.status === 0) {
    mostrarAviso("Sem conexão com o servidor. Confira se ele está ligado e recarregue a página.");
  } else {
    mostrarAviso(erro instanceof Error ? erro.message : "Algo deu errado ao carregar a linha do tempo.");
  }
}

quandoPerderSessao(recomecar);
ligarMenuDeCriar();
$("#botao-conta").addEventListener("click", () => {
  if (conta) void abrirConta($<HTMLDialogElement>("#conta"), conta, recomecar);
});
iniciar().catch(tratarErro);
