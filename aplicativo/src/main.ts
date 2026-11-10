import "./estilo/base.css";
import { semanaDeVida } from "./semanas";

// Data fictícia, só para a página de exemplo.
const NASCIMENTO_EXEMPLO = new Date(1990, 2, 14);

const semana = document.querySelector<HTMLParagraphElement>("#semana")!;
semana.textContent = `Semana ${semanaDeVida(NASCIMENTO_EXEMPLO, new Date()).toLocaleString("pt-BR")} de uma vida de exemplo`;

const servidor = document.querySelector<HTMLParagraphElement>("#servidor")!;

async function verificarServidor(): Promise<void> {
  try {
    const resposta = await fetch("/api/saude");
    if (!resposta.ok) throw new Error(`HTTP ${resposta.status}`);
    const dados: { status: string; versao: string } = await resposta.json();
    servidor.textContent = `Servidor no ar · versão ${dados.versao}`;
    servidor.dataset.estado = "ok";
  } catch {
    servidor.textContent = "Servidor fora do ar. Inicie-o com: uvicorn app.principal:app --reload";
    servidor.dataset.estado = "erro";
  }
}

verificarServidor();
