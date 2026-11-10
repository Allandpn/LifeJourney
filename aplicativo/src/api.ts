// Conversa com o servidor. Todas as chamadas passam por aqui.

import type { Capitulo, Estimativa, Intencao, Memoria, Perfil, Sexo } from "./tipos";

export class ErroDaApi extends Error {
  constructor(public status: number, mensagem: string) {
    super(mensagem);
  }
}

async function pedir<T>(caminho: string, opcoes: RequestInit = {}): Promise<T> {
  let resposta: Response;
  try {
    resposta = await fetch(caminho, {
      ...opcoes,
      headers: { "Content-Type": "application/json", ...opcoes.headers },
      credentials: "same-origin",
    });
  } catch {
    throw new ErroDaApi(0, "Sem conexão com o servidor.");
  }
  if (!resposta.ok) {
    let mensagem = `Erro ${resposta.status}`;
    try {
      const corpo = await resposta.json();
      if (typeof corpo.detail === "string") mensagem = corpo.detail;
    } catch {
      // a resposta não era JSON; fica a mensagem genérica
    }
    throw new ErroDaApi(resposta.status, mensagem);
  }
  return resposta.status === 204 ? (undefined as T) : resposta.json();
}

export const api = {
  perfil: () => pedir<Perfil>("/api/perfil"),
  salvarPerfil: (nascimento: string, sexo: Sexo) =>
    pedir<Perfil>("/api/perfil", { method: "PUT", body: JSON.stringify({ nascimento, sexo }) }),
  memorias: () => pedir<Memoria[]>("/api/memorias"),
  capitulos: () => pedir<Capitulo[]>("/api/capitulos"),
  intencoes: () => pedir<Intencao[]>("/api/intencoes"),
  estimativa: () => pedir<Estimativa>("/api/estimativa"),
};
