import { describe, expect, it } from "vitest";
import { idadeEm, lerData, semanaDeVida } from "./tempo";

const nascimento = lerData("1990-03-14");

describe("semanaDeVida", () => {
  it("conta o dia do nascimento como semana 1", () => {
    expect(semanaDeVida(nascimento, lerData("1990-03-14"))).toBe(1);
  });

  it("muda de semana a cada 7 dias", () => {
    expect(semanaDeVida(nascimento, lerData("1990-03-20"))).toBe(1);
    expect(semanaDeVida(nascimento, lerData("1990-03-21"))).toBe(2);
  });

  it("não aceita data anterior ao nascimento", () => {
    expect(() => semanaDeVida(nascimento, lerData("1990-03-13"))).toThrow(RangeError);
  });
});

describe("idadeEm", () => {
  it("só completa o ano no dia do aniversário", () => {
    expect(idadeEm(nascimento, lerData("2026-03-13"))).toBe(35);
    expect(idadeEm(nascimento, lerData("2026-03-14"))).toBe(36);
  });
});
