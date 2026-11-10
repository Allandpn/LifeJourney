import "./estilo/base.css";
import "./estilo/linha-do-tempo.css";
import "./estilo/formularios.css";
import { api, ErroDaApi } from "./api";
import { type Dados, TelaDaLinhaDoTempo } from "./linha-do-tempo/tela";
import { mostrarBoasVindas } from "./telas/boas-vindas";
import { formularioDeCapitulo, formularioDeIntencao, formularioDeMemoria, hojeIso } from "./telas/formularios";

const $ = <T extends HTMLElement>(seletor: string) => document.querySelector<T>(seletor)!;

let tela: TelaDaLinhaDoTempo | null = null;
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

async function iniciar(): Promise<void> {
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
  if (erro instanceof ErroDaApi && erro.status === 0) {
    mostrarAviso("Sem conexão com o servidor. Confira se ele está ligado e recarregue a página.");
  } else {
    mostrarAviso(erro instanceof Error ? erro.message : "Algo deu errado ao carregar a linha do tempo.");
  }
}

ligarMenuDeCriar();
iniciar().catch(tratarErro);
