// Formato dos dados que vêm da API (servidor/app/esquemas.py).

export type Sexo = "masculino" | "feminino";
export type Emocao = "alegria" | "calma" | "orgulho" | "saudade" | "tristeza" | "incerteza";
export type CorCapitulo = "menta" | "azul" | "ambar" | "laranja" | "rosa" | "lavanda" | "coral";
export type StatusIntencao = "ativa" | "pausada" | "virou_memoria" | "deixada_de_lado";

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
}

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

export interface Estimativa {
  base: string;
  versao_config: string;
  hr_total: number;
  expectativa_media: number;
  p10: number;
  mediana: number;
  p90: number;
  sobrevivencia: [number, number][]; // (idade, chance de estar vivo)
}
