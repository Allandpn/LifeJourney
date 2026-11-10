# 7. Roteiro

Cada etapa termina com algo que funciona e pode ser visto. Até a etapa 6, tudo roda no computador de desenvolvimento.

| Etapa | Entrega | Pronto quando |
|---|---|---|
| 0. Preparação | Pasta `servidor/` com Python e pytest; pasta `aplicativo/` com TypeScript e Vite | Um teste de exemplo passa e uma página de exemplo abre |
| 1. Núcleo de cálculo | Curva de sobrevivência e percentis em Python, com tábua provisória (Gompertz) e fatores em configuração | Testes de limites e de perfil médio passam; o caso de teste pessoal (fora do git) dá valores próximos aos do protótipo de cálculo |
| 2. Banco e API | Tabelas e rotas para memórias, capítulos e intenções | Dá para criar e listar registros pela documentação automática da API |
| 3. Linha do tempo no celular | A tela do protótipo, com layout de celular primeiro, lendo da API | Rolagem, granularidade, minimapa e "Hoje" funcionam com dados de exemplo |
| 4. Registro | Criar e editar memórias (com foto), capítulos e intenções pelo aplicativo | O que é registrado continua lá ao reabrir |
| 5. Login | Entrar, sair, trocar senha; todas as rotas protegidas | Sem login nada é devolvido |
| 6. Questionário e "e se?" | Tela de perguntas, faixa estimada e ganhos; o futuro da linha passa a usar o resultado | Responder muda o futuro da linha |
| 7. Publicação | Servidor na internet com HTTPS; aplicativo instalável no celular | Registrar no celular e ver no computador |
| 8. Backup | Exportar e importar o ZIP; indicador de último backup | Importar em um servidor limpo recupera tudo |
| 9. Tábua real | Tábua do IBGE 2024 no lugar da provisória; fatores conferidos | Teste de importação bate com os valores de referência |

A etapa 9 depende das pendências científicas listadas em [Modelo de cálculo](05-modelo-de-calculo.md) e pode ser adiantada.

Ficam para depois da v1: registrar sem conexão, revisão periódica de fase, senha por memória, incerteza dos riscos relativos.
