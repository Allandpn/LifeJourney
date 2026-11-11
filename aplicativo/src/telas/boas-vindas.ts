// Primeiro acesso: pede só a data de nascimento e o sexo.

import { api } from "../api";
import type { Sexo } from "../tipos";

export function mostrarBoasVindas(el: HTMLElement, aoTerminar: () => void): void {
  const hoje = new Date().toISOString().slice(0, 10);
  el.hidden = false;
  el.innerHTML = `
    <form class="boas-vindas" id="form-boas-vindas">
      <span class="etiqueta">Primeiro acesso</span>
      <h1>Vida em <span>Semanas</span></h1>
      <p>Para desenhar a sua linha do tempo, precisamos só de duas coisas. O sexo é usado na estimativa de vida, que parte da tábua de mortalidade do IBGE.</p>
      <label>Data de nascimento <input type="date" id="nascimento" required min="1900-01-01" max="${hoje}"></label>
      <fieldset>
        <legend>Sexo</legend>
        <label class="opcao"><input type="radio" name="sexo" value="feminino" required> feminino</label>
        <label class="opcao"><input type="radio" name="sexo" value="masculino"> masculino</label>
      </fieldset>
      <p class="erro" id="erro-boas-vindas" hidden></p>
      <button type="submit" class="botao principal">Ver minha linha</button>
      <p class="ajuda">Já tem um arquivo exportado do Vida em Semanas?
        <label class="ligacao-discreta"><input type="file" accept=".zip,application/zip" id="importar-inicio" hidden>Importar e continuar de onde parou</label></p>
    </form>`;

  const form = el.querySelector<HTMLFormElement>("#form-boas-vindas")!;
  form.querySelector<HTMLInputElement>("#importar-inicio")!.addEventListener("change", async (e) => {
    const arquivo = (e.target as HTMLInputElement).files?.[0];
    if (!arquivo) return;
    const erro = form.querySelector<HTMLElement>("#erro-boas-vindas")!;
    try {
      const resultado = await api.dados.importar(arquivo);
      if (!resultado.perfil_preenchido) {
        erro.textContent = "Importado, mas o arquivo não tinha data de nascimento. Preencha acima para continuar.";
        erro.hidden = false;
        return;
      }
      el.hidden = true;
      aoTerminar();
    } catch (falha) {
      erro.textContent = falha instanceof Error ? falha.message : "Não foi possível importar.";
      erro.hidden = false;
    }
  });
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const nascimento = form.querySelector<HTMLInputElement>("#nascimento")!.value;
    const sexo = form.querySelector<HTMLInputElement>('input[name="sexo"]:checked')?.value as Sexo;
    const erro = form.querySelector<HTMLElement>("#erro-boas-vindas")!;
    try {
      await api.salvarPerfil(nascimento, sexo);
      el.hidden = true;
      aoTerminar();
    } catch (falha) {
      erro.textContent = falha instanceof Error ? falha.message : "Não foi possível salvar.";
      erro.hidden = false;
    }
  });
}
