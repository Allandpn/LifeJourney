import "./estilo/base.css";
import "./estilo/linha-do-tempo.css";
import { api, ErroDaApi } from "./api";
import { TelaDaLinhaDoTempo } from "./linha-do-tempo/tela";
import { mostrarBoasVindas } from "./telas/boas-vindas";

const $ = <T extends HTMLElement>(seletor: string) => document.querySelector<T>(seletor)!;

function mostrarAviso(texto: string): void {
  const aviso = $("#aviso");
  aviso.textContent = texto;
  aviso.hidden = false;
}

async function iniciar(): Promise<void> {
  const perfil = await api.perfil();
  if (!perfil.nascimento || !perfil.sexo) {
    document.body.dataset.tela = "boas-vindas";
    mostrarBoasVindas($("#boas-vindas"), () => void iniciar().catch(tratarErro));
    return;
  }
  const [memorias, capitulos, intencoes, estimativa] = await Promise.all([
    api.memorias(), api.capitulos(), api.intencoes(), api.estimativa(),
  ]);
  document.body.dataset.tela = "linha";
  new TelaDaLinhaDoTempo(
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
    { nascimento: perfil.nascimento, memorias, capitulos, intencoes, estimativa },
  ).iniciar();
}

function tratarErro(erro: unknown): void {
  if (erro instanceof ErroDaApi && erro.status === 0) {
    mostrarAviso("Sem conexão com o servidor. Confira se ele está ligado e recarregue a página.");
  } else {
    mostrarAviso(erro instanceof Error ? erro.message : "Algo deu errado ao carregar a linha do tempo.");
  }
}

iniciar().catch(tratarErro);
