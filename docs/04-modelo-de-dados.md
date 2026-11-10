# 4. Modelo de dados

## Regras gerais

- Toda entidade tem `id` (texto único), `criadoEm` e `atualizadoEm`.
- Toda entidade pertence a um usuário (`usuarioId`). Hoje há um só, mas o modelo não impede outros.
- Apagar marca o registro com `excluidoEm` em vez de removê-lo. Assim os outros aparelhos ficam sabendo da exclusão ao sincronizar.
- **Guardamos datas, não números de semana.** A semana de vida é calculada a partir da data de nascimento. Assim nada precisa ser recalculado se a data de nascimento for corrigida.
- Datas sem hora usam o formato `AAAA-MM-DD`.
- Os nomes de campos ficam em português, como no restante do projeto.

## Usuário

| Campo | Tipo | Observação |
|---|---|---|
| `email` | texto | Usado para entrar |
| `senhaHash` | texto | A senha nunca é guardada; só um código derivado dela |
| `nascimento` | data | Obrigatório |
| `sexo` | `masculino` ou `feminino` | Necessário para a tábua do IBGE |
| `ultimoBackup` | data e hora | Opcional |

## Memória

| Campo | Tipo | Observação |
|---|---|---|
| `data` | data | Obrigatório; não pode ser futura |
| `texto` | texto | Obrigatório; limite de 280 caracteres (em avaliação) |
| `foto` | referência a arquivo | Opcional; uma foto por memória na v1. O arquivo fica no servidor, em versão reduzida |
| `emocao` | texto | Opcional: alegria, calma, orgulho, saudade, tristeza, incerteza |
| `intensidade` | 1, 2 ou 3 | Leve, média, forte; padrão 2 |
| `marcante` | sim/não | Memórias marcantes têm prioridade no nível Ano |
| `silenciar` | sim/não | Se sim, fica fora de "nesta semana, em outros anos" |
| `veioDe` | lista de ids de memórias | A ligação causal; "levou a" é o caminho inverso, calculado |
| `tags` | lista de textos | Opcional |

## Capítulo

| Campo | Tipo | Observação |
|---|---|---|
| `nome` | texto | Obrigatório |
| `inicio` | data | Obrigatório |
| `fim` | data | Vazio significa "em andamento" |
| `cor` | nome da paleta | Uma das sete cores de capítulo |
| `principal` | sim/não | Capítulos principais definem a cor da época |
| `categoria` | texto | Opcional: trabalho, relacionamento, saúde, transição... |
| `notas` | texto longo | Opcional |

Capítulos podem se sobrepor. Se dois capítulos principais se sobrepõem, vale o que começou primeiro.

## Intenção

| Campo | Tipo | Observação |
|---|---|---|
| `nome` | texto | Obrigatório |
| `horizonte` | ver abaixo | Obrigatório |
| `status` | `ativa`, `pausada`, `virou memória`, `deixada de lado` | Nunca "concluída / não concluída" |
| `notas` | texto | Opcional |
| `memoriaId` | id de memória | Preenchido quando a intenção vira memória |

O horizonte tem três formas:

| Forma | Campos | Exemplo |
|---|---|---|
| Data | `data` | abril de 2027 |
| Intervalo | `de`, `ate` | entre 2027 e 2028 |
| Algum dia | nenhum | sem data |

## Respostas do questionário

Cada vez que o usuário responde, guarda-se um registro novo. O histórico permite comparar a estimativa ao longo do tempo.

| Campo | Tipo | Observação |
|---|---|---|
| `data` | data | Quando respondeu |
| `respostas` | fator → resposta | Pergunta pulada fica ausente e conta como a média brasileira |
| `versaoConfig` | texto | Versão do arquivo de fatores usada no cálculo |
| `resultado` | percentis 10, 50, 90 e risco total | Guardado para comparação histórica |

## Backup

A exportação gera um arquivo ZIP com:

- `dados.json`: todas as entidades acima, com um número de versão do formato;
- `fotos/`: os arquivos de imagem, nomeados pelo id da memória;
- `memorias.md`: as memórias em texto legível, agrupadas por capítulo, para leitura sem o aplicativo.

A importação casa os registros pelo `id`. Registro com o mesmo id é atualizado se o do arquivo for mais recente; nada é duplicado.
