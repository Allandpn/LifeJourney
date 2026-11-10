# LifeJourney — Vida em Semanas

Aplicativo pessoal que mostra a vida como uma linha do tempo rolável. O passado é um histórico de memórias e capítulos, o presente é a semana atual, e o futuro é um espaço aberto cuja forma vem de uma estimativa de longevidade baseada na tábua de mortalidade do IBGE.

O uso principal é no celular. Cada pessoa tem a própria conta, e os dados ficam sincronizados entre os aparelhos por um servidor próprio, hospedado em um Raspberry Pi.

## Estado atual

Etapa 0 do [roteiro](docs/07-roteiro.md) concluída: o servidor em Python e o aplicativo em TypeScript existem, se conversam e têm os primeiros testes. Ainda não há funcionalidades do sistema.

- Protótipo visual: [`prototipo/linha-do-tempo.html`](prototipo/linha-do-tempo.html) (abrir no navegador)

## Como rodar no computador

Você precisa de **Python 3.12 ou mais novo** e **Node.js 20 ou mais novo**. Os comandos abaixo valem para o terminal do IntelliJ no Windows (PowerShell); no Linux ou macOS, troque `.venv\Scripts\` por `.venv/bin/`.

São dois terminais, um para cada parte.

### Terminal 1: servidor (Python)

Na primeira vez:

```powershell
cd servidor
python -m venv .venv
.venv\Scripts\pip install -e ".[dev]"
```

Para rodar os testes:

```powershell
.venv\Scripts\pytest
```

Para ligar o servidor (fica em http://127.0.0.1:8000; a documentação automática da API fica em http://127.0.0.1:8000/docs):

```powershell
.venv\Scripts\uvicorn app.principal:app --reload
```

### Terminal 2: aplicativo (TypeScript)

Na primeira vez:

```powershell
cd aplicativo
npm install
```

Para rodar os testes:

```powershell
npm test
```

Para abrir o aplicativo (fica em http://localhost:5173):

```powershell
npm run dev
```

Com o servidor ligado, a página mostra "Servidor no ar". Para ver no celular, conecte-o à mesma rede Wi-Fi e abra o endereço "Network" que o `npm run dev` mostra.

### No IntelliJ

- Abra a pasta `LifeJourney` inteira como projeto.
- Instale o plugin **Python** (no IntelliJ Community) e aponte o interpretador do projeto para `servidor\.venv\Scripts\python.exe`.
- Marque a pasta `servidor` como "Sources Root" para o IntelliJ achar o pacote `app`.

## Organização

| Pasta | Conteúdo |
|---|---|
| `servidor/app/` | Código do servidor e, a partir da etapa 1, o núcleo de cálculo |
| `servidor/testes/` | Testes do servidor (pytest) |
| `aplicativo/src/` | Telas e lógica de exibição; testes ficam ao lado do código, em `*.test.ts` |
| `docs/` | Documentação |
| `prototipo/` | Protótipo visual, só como referência |

## Documentação

| Documento | Conteúdo |
|---|---|
| [Visão](docs/01-visao.md) | O que é, para quem, princípios e escopo da v1 |
| [Experiência](docs/02-experiencia.md) | A linha do tempo, granularidade, minimapa e telas |
| [Design visual](docs/03-design-visual.md) | Cores, tipografia e regras de estilo |
| [Modelo de dados](docs/04-modelo-de-dados.md) | Memória, Capítulo, Intenção e demais entidades |
| [Modelo de cálculo](docs/05-modelo-de-calculo.md) | Tábua do IBGE, fatores de risco e a faixa estimada |
| [Arquitetura](docs/06-arquitetura.md) | Tecnologias, pastas e módulos, com o porquê de cada escolha |
| [Roteiro](docs/07-roteiro.md) | Etapas de construção |
| [Decisões](docs/08-decisoes.md) | O que já foi decidido, o que está proposto e o que está em aberto |

## Privacidade

Este repositório é público. Por isso:

- dados reais de saúde e casos de teste pessoais não entram nele (a pasta `dados-pessoais/` está no `.gitignore`);
- senhas, chaves e endereços do servidor ficam em um arquivo `.env`, também fora do git;
- todos os dados de exemplo são fictícios.
