# 7. Roteiro

Cada etapa termina com algo que funciona e pode ser visto.

| Etapa | Entrega | Pronto quando |
|---|---|---|
| 0. Preparação | Projeto com TypeScript, Vite e Vitest; tipos das entidades | Um teste de exemplo passa |
| 1. Núcleo de cálculo | Curva de sobrevivência e percentis, com tábua provisória (Gompertz) e fatores em configuração | Testes de limites e de perfil médio passam; o caso de teste pessoal dá valores próximos aos do protótipo de cálculo |
| 2. Núcleo de tempo | Semanas de vida, períodos por granularidade, agrupamento de vazios | Testes passam |
| 3. Linha do tempo | A tela do protótipo, agora sobre o núcleo, com dados de exemplo | Rolagem, granularidade, minimapa e "Hoje" funcionam |
| 4. Registro | Criar e editar memórias (com foto), capítulos e intenções; armazenamento local | Os dados continuam lá depois de fechar o navegador |
| 5. Questionário e "e se?" | Tela de perguntas, faixa estimada e ganhos; o futuro da linha passa a usar o resultado | Responder muda o futuro da linha |
| 6. Backup | Exportar e importar o ZIP; indicador de último backup | Importar em um navegador limpo recupera tudo |
| 7. Tábua real | Tábua do IBGE 2024 no lugar da provisória; fatores conferidos | Teste de importação bate com os valores de referência |
| 8. Celular | PWA instalável; ajustes de toque | O aplicativo abre pelo ícone, sem internet |

A etapa 7 depende das pendências científicas listadas em [Modelo de cálculo](05-modelo-de-calculo.md) e pode ser adiantada.

Ficam para depois da v1: revisão periódica de fase, senha por memória, incerteza dos riscos relativos.
