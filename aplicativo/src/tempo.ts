// Datas e semanas de vida. Datas sem hora são tratadas como meia-noite local.

export const DIA = 24 * 60 * 60 * 1000;
export const SEMANA = 7 * DIA;
export const ANO = 365.2425 * DIA;

export const MESES = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"];
export const MESES_LONGOS = [
  "janeiro", "fevereiro", "março", "abril", "maio", "junho",
  "julho", "agosto", "setembro", "outubro", "novembro", "dezembro",
];

/** "2018-11-05" -> instante da meia-noite local desse dia. */
export function lerData(texto: string): number {
  const [ano, mes, dia] = texto.split("-").map(Number);
  return new Date(ano, mes - 1, dia).getTime();
}

/** Meia-noite local do dia de `instante`. */
export function inicioDoDia(instante: number): number {
  const d = new Date(instante);
  return new Date(d.getFullYear(), d.getMonth(), d.getDate()).getTime();
}

/** Idade em anos completos na data `instante` (aniversário conta no próprio dia). */
export function idadeEm(nascimento: number, instante: number): number {
  const n = new Date(nascimento);
  const d = new Date(instante);
  let idade = d.getFullYear() - n.getFullYear();
  if (d.getMonth() < n.getMonth() || (d.getMonth() === n.getMonth() && d.getDate() < n.getDate())) idade--;
  return idade;
}

/** Instante em que a pessoa completa `anos` de idade (aceita fração). */
export function instanteNaIdade(nascimento: number, anos: number): number {
  return nascimento + anos * ANO;
}

/** Semana de vida de `instante` (a semana do nascimento é a 1). */
export function semanaDeVida(nascimento: number, instante: number): number {
  const dias = Math.round((inicioDoDia(instante) - inicioDoDia(nascimento)) / DIA);
  if (dias < 0) throw new RangeError("A data é anterior ao nascimento.");
  return Math.floor(dias / 7) + 1;
}

export function ano(instante: number): number {
  return new Date(instante).getFullYear();
}

export function formatarData(instante: number): string {
  const d = new Date(instante);
  return `${d.getDate()} ${MESES[d.getMonth()]} ${d.getFullYear()}`;
}

export function formatarNumero(n: number): string {
  return n.toLocaleString("pt-BR");
}
