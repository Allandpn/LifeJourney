import { describe, expect, it } from "vitest";
import { semanaDeVida } from "./semanas";

describe("semanaDeVida", () => {
  const nascimento = new Date(1990, 2, 14);

  it("conta o dia do nascimento como semana 1", () => {
    expect(semanaDeVida(nascimento, new Date(1990, 2, 14))).toBe(1);
  });

  it("muda de semana a cada 7 dias", () => {
    expect(semanaDeVida(nascimento, new Date(1990, 2, 20))).toBe(1);
    expect(semanaDeVida(nascimento, new Date(1990, 2, 21))).toBe(2);
  });

  it("não aceita data anterior ao nascimento", () => {
    expect(() => semanaDeVida(nascimento, new Date(1990, 2, 13))).toThrow(RangeError);
  });
});
