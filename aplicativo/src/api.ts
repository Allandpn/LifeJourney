// Conversa com o servidor. Todas as chamadas passam por aqui.

import type {
  Capitulo, CapituloDados, Estimativa, Intencao, IntencaoDados, Memoria, MemoriaDados, Perfil, Sexo,
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
  perfil: () => pedir<Perfil>("/api/perfil"),
  salvarPerfil: (nascimento: string, sexo: Sexo) => pedir<Perfil>("/api/perfil", json("PUT", { nascimento, sexo })),
  estimativa: () => pedir<Estimativa>("/api/estimativa"),

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
