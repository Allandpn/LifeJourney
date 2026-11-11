// Formato dos dados que vêm da API (servidor/app/esquemas.py).

export type Sexo = "masculino" | "feminino";
export type Emocao = "alegria" | "calma" | "orgulho" | "saudade" | "tristeza" | "incerteza";
export type CorCapitulo = "menta" | "azul" | "ambar" | "laranja" | "rosa" | "lavanda" | "coral";
export type StatusIntencao = "ativa" | "pausada" | "virou_memoria" | "deixada_de_lado";

export interface Conta {
  email: string;
  administrador: boolean;
}

export interface SessaoConectada {
  id: string;
  aparelho: string;
  criado_em: string;
  ultimo_uso: string;
  esta: boolean;
}

export interface Convite {
  id: string;
  criado_em: string;
  valido_ate: string;
  usado: boolean;
  cancelado: boolean;
}

export interface ResumoDaImportacao {
  perfil_preenchido: boolean;
  resumo: Record<string, { criados: number; atualizados: number; mantidos: number; recusados: number }>;
}

export interface LinkGerado {
  caminho: string;
  valido_ate: string;
}

export interface Perfil {
  email: string;
  nascimento: string | null; // "AAAA-MM-DD"
  sexo: Sexo | null;
  ultimo_backup: string | null;
}

export interface Memoria {
  id: string;
  data: string;
  texto: string;
  emocao: Emocao | null;
  intensidade: 1 | 2 | 3;
  marcante: boolean;
  silenciar: boolean;
  veio_de: string[];
  levou_a: string[];
  tags: string[];
  foto: string | null; // endereço da foto na API
}

/** O que o aplicativo envia para criar ou alterar uma memória. */
export type MemoriaDados = Pick<Memoria, "data" | "texto" | "emocao" | "intensidade" | "marcante" | "silenciar" | "veio_de">;
export type CapituloDados = Omit<Capitulo, "id">;
export type IntencaoDados = Omit<Intencao, "id">;

export interface Capitulo {
  id: string;
  nome: string;
  inicio: string;
  fim: string | null; // null = em andamento
  cor: CorCapitulo;
  principal: boolean;
  categoria: string | null;
  notas: string | null;
}

export type Horizonte =
  | { tipo: "data"; data: string }
  | { tipo: "intervalo"; de: string; ate: string }
  | { tipo: "algum_dia" };

export interface Intencao {
  id: string;
  nome: string;
  horizonte: Horizonte;
  status: StatusIntencao;
  notas: string | null;
  memoria_id: string | null;
}

export interface Mudanca {
  fator: string; // ou "todas"
  acao: string;
  hr_total: number;
  ganho_semanas: number;
  mediana: number;
}

export interface Pergunta {
  fator: string;
  pergunta: string;
  tipo: "opcoes" | "altura_e_peso";
  opcoes: { valor: string; rotulo: string }[];
  fonte: string;
  muda_com_habito: boolean;
}

export interface EnvioDeRespostas {
  respostas: Record<string, string>;
  altura_m: number | null;
  peso_kg: number | null;
}

export interface RodadaDeRespostas extends EnvioDeRespostas {
  id: string;
  criado_em: string;
  resultado: { idade: number; hr_total: number; expectativa_media: number; p10: number; mediana: number; p90: number };
}

export interface Estimativa {
  base: "brasileiro_medio" | "questionario";
  respondido_em: string | null;
  e_se: Mudanca[];
  versao_config: string;
  hr_total: number;
  expectativa_media: number;
  p10: number;
  mediana: number;
  p90: number;
  sobrevivencia: [number, number][]; // (idade, chance de estar vivo)
}
