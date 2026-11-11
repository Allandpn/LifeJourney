import { describe, expect, it } from "vitest";
import { descreverAparelho, descreverImportacao, precisaDeBackup } from "./conta";

describe("precisaDeBackup", () => {
  const agora = new Date("2026-11-11T12:00:00Z").getTime();
  it("lembra quem nunca exportou ou exportou há mais de 30 dias", () => {
    expect(precisaDeBackup(null, agora)).toBe(true);
    expect(precisaDeBackup("2026-10-01T12:00:00Z", agora)).toBe(true);
    expect(precisaDeBackup("2026-11-01T12:00:00Z", agora)).toBe(false);
  });
});

describe("descreverImportacao", () => {
  it("resume o que mudou em português", () => {
    const texto = descreverImportacao({
      perfil_preenchido: true,
      resumo: {
        memorias: { criados: 2, atualizados: 0, mantidos: 1, recusados: 0 },
        capitulos: { criados: 0, atualizados: 1, mantidos: 0, recusados: 1 },
      },
    });
    expect(texto).toBe("Importado. perfil preenchido com o do arquivo; memórias: 2 novas, 1 sem mudança; "
      + "capítulos: 1 atualizados, 1 recusados por dados inválidos.");
  });
});

describe("descreverAparelho", () => {
  it("reconhece navegador e sistema", () => {
    expect(descreverAparelho("Mozilla/5.0 (Linux; Android 14) AppleWebKit/537.36 Chrome/131.0 Mobile Safari/537.36")).toBe("Chrome no Android");
    expect(descreverAparelho("Mozilla/5.0 (Windows NT 10.0) Gecko/20100101 Firefox/133.0")).toBe("Firefox no Windows");
    expect(descreverAparelho("")).toBe("Aparelho desconhecido");
  });
});
