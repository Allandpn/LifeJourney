// Conversa com o servidor. Todas as chamadas passam por aqui.

import type {
  Capitulo, CapituloDados, Conta, Convite, EnvioDeRespostas, Estimativa, Intencao, IntencaoDados, LinkGerado, Memoria,
  MemoriaDados, Perfil, Pergunta, ResumoDaImportacao, RodadaDeRespostas, SessaoConectada, Sexo,
} from "./tipos";

export class ErroDaApi extends Error {
  constructor(public status: number, mensagem: string) {
    super(mensagem);
  }
}

/** Transforma a resposta de erro da API num texto legível. */
function mensagemDeErro(status: number, corpo: unknown): string {
  const detalhe = (corpo as { detail?: unknown })?.detail;
  if (typeof detalhe === "string") return detalhe;
  if (Array.isArray(detalhe)) {
    // erros de validação: uma lista com a mensagem de cada campo
    return detalhe
      .map((d: { msg?: string }) => (d.msg ?? "").replace(/^Value error, /, ""))
      .filter(Boolean)
      .join(" ");
  }
  if (status === 413) return "O arquivo é grande demais.";
  return `Erro ${status}.`;
}

/** Chamado quando a sessão acaba no meio do uso (saiu em outro aparelho, trocou a senha...). */
let aoPerderSessao: () => void = () => {};
export function quandoPerderSessao(acao: () => void): void {
  aoPerderSessao = acao;
}
// nestas rotas, 401 é uma resposta normal (senha errada, ou ainda não entrou)
const ROTAS_SEM_SESSAO = new Set(["/api/entrar", "/api/conta"]);

async function pedir<T>(caminho: string, opcoes: RequestInit = {}): Promise<T> {
  const ehJson = typeof opcoes.body === "string";
  let resposta: Response;
  try {
    resposta = await fetch(caminho, {
      ...opcoes,
      headers: { ...(ehJson ? { "Content-Type": "application/json" } : {}), ...opcoes.headers },
      credentials: "same-origin",
    });
  } catch {
    throw new ErroDaApi(0, "Sem conexão com o servidor.");
  }
  if (!resposta.ok) {
    let corpo: unknown = null;
    try {
      corpo = await resposta.json();
    } catch {
      // a resposta não era JSON
    }
    if (resposta.status === 401 && !ROTAS_SEM_SESSAO.has(caminho)) aoPerderSessao();
    throw new ErroDaApi(resposta.status, mensagemDeErro(resposta.status, corpo));
  }
  return resposta.status === 204 ? (undefined as T) : resposta.json();
}

const json = (metodo: string, dados: unknown): RequestInit => ({ method: metodo, body: JSON.stringify(dados) });

function crud<Lido, Dados>(base: string) {
  return {
    listar: () => pedir<Lido[]>(base),
    criar: (dados: Dados) => pedir<Lido>(base, json("POST", dados)),
    alterar: (id: string, dados: Partial<Dados>) => pedir<Lido>(`${base}/${id}`, json("PATCH", dados)),
    excluir: (id: string) => pedir<void>(`${base}/${id}`, { method: "DELETE" }),
  };
}

export const api = {
  conta: () => pedir<Conta>("/api/conta"),
  entrar: (email: string, senha: string) => pedir<Conta>("/api/entrar", json("POST", { email, senha })),
  sair: () => pedir<void>("/api/sair", { method: "POST" }),
  criarConta: (codigo: string, email: string, senha: string) =>
    pedir<Conta>("/api/contas", json("POST", { codigo, email, senha })),
  redefinirSenha: (codigo: string, senha_nova: string) =>
    pedir<void>("/api/redefinir-senha", json("POST", { codigo, senha_nova })),
  trocarSenha: (senha_atual: string, senha_nova: string) =>
    pedir<void>("/api/conta/senha", json("POST", { senha_atual, senha_nova })),
  sessoes: () => pedir<SessaoConectada[]>("/api/conta/sessoes"),
  desconectar: (id: string) => pedir<void>(`/api/conta/sessoes/${id}`, { method: "DELETE" }),
  dados: {
    /** Baixa o ZIP com tudo da conta e devolve o arquivo e o nome sugerido. */
    exportar: async (): Promise<{ arquivo: Blob; nome: string }> => {
      let resposta: Response;
      try {
        resposta = await fetch("/api/exportacao", { credentials: "same-origin" });
      } catch {
        throw new ErroDaApi(0, "Sem conexão com o servidor.");
      }
      if (resposta.status === 401) aoPerderSessao();
      if (!resposta.ok) throw new ErroDaApi(resposta.status, "Não foi possível exportar.");
      const nome = /filename="([^"]+)"/.exec(resposta.headers.get("content-disposition") ?? "")?.[1] ?? "vida-em-semanas.zip";
      return { arquivo: await resposta.blob(), nome };
    },
    importar: (arquivo: Blob) => {
      const formulario = new FormData();
      formulario.append("arquivo", arquivo, "dados.zip");
      return pedir<ResumoDaImportacao>("/api/importacao", { method: "POST", body: formulario });
    },
    apagarConta: (senha: string) => pedir<void>("/api/conta/apagar", json("POST", { senha })),
  },
  admin: {
    criarConvite: () => pedir<LinkGerado>("/api/admin/convites", { method: "POST" }),
    convites: () => pedir<Convite[]>("/api/admin/convites"),
    cancelarConvite: (id: string) => pedir<void>(`/api/admin/convites/${id}`, { method: "DELETE" }),
    criarRedefinicao: (email: string) => pedir<LinkGerado>("/api/admin/redefinicoes", json("POST", { email })),
  },

  perfil: () => pedir<Perfil>("/api/perfil"),
  salvarPerfil: (nascimento: string, sexo: Sexo) => pedir<Perfil>("/api/perfil", json("PUT", { nascimento, sexo })),
  estimativa: () => pedir<Estimativa>("/api/estimativa"),
  questionario: {
    perguntas: () => pedir<Pergunta[]>("/api/questionario"),
    responder: (envio: EnvioDeRespostas) => pedir<Estimativa>("/api/questionario/respostas", json("POST", envio)),
    historico: () => pedir<RodadaDeRespostas[]>("/api/questionario/respostas"),
    apagar: () => pedir<void>("/api/questionario/respostas", { method: "DELETE" }),
  },

  memorias: {
    ...crud<Memoria, MemoriaDados>("/api/memorias"),
    enviarFoto: (id: string, arquivo: Blob) => {
      const formulario = new FormData();
      formulario.append("arquivo", arquivo, "foto");
      return pedir<Memoria>(`/api/memorias/${id}/foto`, { method: "PUT", body: formulario });
    },
    removerFoto: (id: string) => pedir<Memoria>(`/api/memorias/${id}/foto`, { method: "DELETE" }),
  },
  capitulos: crud<Capitulo, CapituloDados>("/api/capitulos"),
  intencoes: crud<Intencao, IntencaoDados>("/api/intencoes"),
};
