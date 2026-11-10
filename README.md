# LifeJourney — Vida em Semanas

Aplicativo pessoal que mostra a vida como uma linha do tempo rolável. O passado é um histórico de memórias e capítulos, o presente é a semana atual, e o futuro é um espaço aberto cuja forma vem de uma estimativa de longevidade baseada na tábua de mortalidade do IBGE.

O uso principal é no celular. Cada pessoa tem a própria conta, e os dados ficam sincronizados entre os aparelhos por um servidor próprio, hospedado em um Raspberry Pi.

## Estado atual

Fase de desenho. Existe um protótipo navegável com dados fictícios e esta documentação. Ainda não há código do sistema.

- Protótipo: [`prototipo/linha-do-tempo.html`](prototipo/linha-do-tempo.html) (abrir no navegador)

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
