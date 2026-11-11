# LifeJourney — Vida em Semanas

Aplicativo pessoal que mostra a vida como uma linha do tempo rolável. O passado é um histórico de memórias e capítulos, o presente é a semana atual, e o futuro é um espaço aberto cuja forma vem de uma estimativa de longevidade baseada na tábua de mortalidade do IBGE.

O uso principal é no celular. Cada pessoa tem a própria conta, e os dados ficam sincronizados entre os aparelhos por um servidor próprio, hospedado em um Raspberry Pi.

## Estado atual

Etapas 0 a 6 e 8 do [roteiro](docs/07-roteiro.md) concluídas, e a etapa 7 pronta para instalar no Raspberry Pi ([passo a passo](docs/09-publicacao.md)):

- o servidor em Python e o aplicativo em TypeScript existem, se conversam e têm testes;
- o núcleo de cálculo (`servidor/app/nucleo/`) estima a faixa de vida e o "e se?", com a tábua provisória e todos os números em [`servidor/dados/fatores.json`](servidor/dados/fatores.json).

- o aplicativo mostra a linha do tempo do protótipo, lendo da API: rolagem com granularidade ano, mês e semana, capítulos, "Hoje", futuro com a faixa estimada e minimapa;
- pelo aplicativo dá para criar, editar e excluir memórias (com foto e ligação "veio de"), capítulos e intenções;
- a API grava e devolve memórias, capítulos, intenções e o perfil, num banco SQLite, com cada registro isolado por dono;
- a tela "Estimativa" mostra a faixa provável e o "e se?", com um questionário de saúde opcional; responder muda o futuro da linha do tempo;
- uma imagem Docker reúne o aplicativo e o servidor, com túnel da Cloudflare, cópias de segurança cifradas e o aplicativo instalável no celular;
- cada pessoa pode exportar tudo num ZIP aberto (com as memórias também em texto legível), importar de volta em qualquer conta sem duplicar, e apagar a própria conta;
- cada pessoa tem a sua conta, criada por convite do administrador, com login, troca de senha e lista de aparelhos conectados.

O cálculo usa a tábua real do IBGE 2024 e médias brasileiras do Vigitel 2024 para sete dos dez fatores. Ainda faltam a calibração para os homens e dados brasileiros de três fatores (ver [Modelo de cálculo](docs/05-modelo-de-calculo.md)).

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

Para preencher a conta de desenvolvimento com uma vida fictícia (a mesma do protótipo):

```powershell
.venv\Scripts\python -m app.exemplo
```

Ela cria a conta `dev@exemplo.local`, administradora, com a senha `vida-em-semanas`. Essa senha só serve no seu computador: o servidor em modo produção se recusa a ligar enquanto ela existir.

Para criar a sua conta de administrador de verdade (a senha é pedida no terminal):

```powershell
.venv\Scripts\python -m app.contas criar-admin voce@exemplo.com
```

Para ver o cálculo com um perfil fictício:

```powershell
.venv\Scripts\python -m app.nucleo
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

Com o servidor ligado, a página mostra "Servidor no ar".

Para experimentar a API, abra http://127.0.0.1:8000/docs com o servidor ligado: entre primeiro pela rota `POST /api/entrar`, e o navegador guarda o cookie para as outras. Em modo produção essa página não existe. O banco fica em `dados-pessoais/lifejourney.db` e as fotos em `dados-pessoais/fotos/`; para recomeçar do zero, apague os dois.

As mudanças no banco são aplicadas sozinhas quando o servidor liga (migrações com Alembic). Quem muda uma tabela em `servidor/app/modelos.py` cria a migração, dentro de `servidor`, com:

```powershell
.venv\Scripts\alembic revision --autogenerate -m "o que mudou"
``` Para ver no celular, conecte-o à mesma rede Wi-Fi e abra o endereço "Network" que o `npm run dev` mostra.

### No IntelliJ

- Abra a pasta `LifeJourney` inteira como projeto.
- Instale o plugin **Python** (no IntelliJ Community) e aponte o interpretador do projeto para `servidor\.venv\Scripts\python.exe`.
- Marque a pasta `servidor` como "Sources Root" para o IntelliJ achar o pacote `app`.

## Organização

| Pasta | Conteúdo |
|---|---|
| `servidor/app/` | Código do servidor |
| `servidor/app/nucleo/` | Núcleo de cálculo: tábua, fatores, sobrevivência e "e se?" |
| `servidor/dados/` | Configuração do modelo (`fatores.json`) e, futuramente, a tábua do IBGE |
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
| [Publicação](docs/09-publicacao.md) | Passo a passo para colocar no ar no Raspberry Pi |

## Privacidade

Este repositório é público. Por isso:

- dados reais de saúde e casos de teste pessoais não entram nele (a pasta `dados-pessoais/` está no `.gitignore`);
- senhas, chaves e endereços do servidor ficam em um arquivo `.env`, também fora do git;
- todos os dados de exemplo são fictícios.
