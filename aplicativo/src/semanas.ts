const MS_POR_DIA = 24 * 60 * 60 * 1000;

/**
 * Número da semana de vida em que cai `data` (a semana do nascimento é a 1).
 * Usa datas do calendário local, sem hora, para não errar perto da meia-noite.
 */
export function semanaDeVida(nascimento: Date, data: Date): number {
  const inicio = Date.UTC(nascimento.getFullYear(), nascimento.getMonth(), nascimento.getDate());
  const fim = Date.UTC(data.getFullYear(), data.getMonth(), data.getDate());
  if (fim < inicio) {
    throw new RangeError("A data é anterior ao nascimento.");
  }
  return Math.floor((fim - inicio) / MS_POR_DIA / 7) + 1;
}
