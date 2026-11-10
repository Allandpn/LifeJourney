# 4. Modelo de dados

## Regras gerais

- Toda entidade tem `id` (texto único), `criadoEm` e `atualizadoEm`.
- Toda entidade pertence a um usuário (`usuarioId`). Nenhum dado é compartilhado entre usuários.
- Apagar marca o registro com `excluidoEm` em vez de removê-lo. Assim os outros aparelhos ficam sabendo da exclusão ao sincronizar.
- **Guardamos datas, não números de semana.** A semana de vida é calculada a partir da data de nascimento. Assim nada precisa ser recalculado se a data de nascimento for corrigida.
- Datas sem hora usam o formato `AAAA-MM-DD`.
- Os nomes de campos ficam em português, como no restante do projeto.

## Usuário

| Campo | Tipo | Observação |
|---|---|---|
| `email` | texto | Usado para entrar |
| `senhaHash` | texto | A senha nunca é guardada; só um código derivado dela |
| `administrador` | sim/não | Pode gerar convites e links de redefinição de senha. Não dá acesso aos dados de outras contas pelo aplicativo |
| `nascimento` | data | Obrigatório |
| `sexo` | `masculino` ou `feminino` | Necessário para a tábua do IBGE |
| `ultimoBackup` | data e hora | Opcional |

## Convite

| Campo | Tipo | Observação |
|---|---|---|
| `codigo` | texto aleatório | Vai no link de convite; guardado só como código derivado |
| `validoAte` | data e hora | Expira em poucos dias |
| `usadoPor` | id de usuário | Cada convite cria uma conta só |

## Sessão

Um registro por aparelho conectado. Permite listar os aparelhos e desconectar um deles.

| Campo | Tipo | Observação |
|---|---|---|
| `usuarioId` | id | Dono da sessão |
| `aparelho` | texto | Descrição do navegador e do sistema |
| `ultimoUso` | data e hora | |
| `expiraEm` | data e hora | |

## Memória

| Campo | Tipo | Observação |
|---|---|---|
| `data` | data | Obrigatório; não pode ser futura |
| `texto` | texto | Obrigatório; limite de 280 caracteres (em avaliação) |
| `foto` | referência a arquivo | Opcional; uma foto por memória na v1. O servidor regrava como JPEG de até 1600 px e descarta os metadados (EXIF), que podem conter o local GPS |
| `emocao` | texto | Opcional: `alegria`, `calma`, `orgulho`, `saudade`, `tristeza`, `incerteza` |
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
| `cor` | nome da paleta | `menta`, `azul`, `ambar`, `laranja`, `rosa`, `lavanda` ou `coral` |
| `principal` | sim/não | Capítulos principais definem a cor da época |
| `categoria` | texto | Opcional: trabalho, relacionamento, saúde, transição... |
| `notas` | texto longo | Opcional |

Capítulos podem se sobrepor. Se dois capítulos principais se sobrepõem, vale o que começou primeiro.

## Intenção

| Campo | Tipo | Observação |
|---|---|---|
| `nome` | texto | Obrigatório |
| `horizonte` | ver abaixo | Obrigatório |
| `status` | `ativa`, `pausada`, `virou_memoria`, `deixada_de_lado` | Nunca "concluída / não concluída" |
| `notas` | texto | Opcional |
| `memoriaId` | id de memória | Preenchido quando a intenção vira memória |

O horizonte tem três formas:

| Forma | Como é enviado | Exemplo |
|---|---|---|
| Data | `{"tipo": "data", "data": "2027-04-01"}` | abril de 2027 |
| Intervalo | `{"tipo": "intervalo", "de": "2027-01-01", "ate": "2028-12-31"}` | entre 2027 e 2028 |
| Algum dia | `{"tipo": "algum_dia"}` | sem data |

## Na API

A implementação está em `servidor/app/modelos.py` (tabelas) e `servidor/app/esquemas.py` (validação). Os nomes de campos na API usam `_` (`veio_de`, `criado_em`).

| Rota | Faz |
|---|---|
| `GET` / `PUT /api/perfil` | Lê e grava nascimento e sexo |
| `GET /api/memorias` | Lista em ordem de data; aceita `?de=` e `?ate=` |
| `POST /api/memorias` | Cria |
| `GET` / `PATCH` / `DELETE /api/memorias/{id}` | Lê, altera só os campos enviados, exclui |
| `PUT` / `GET` / `DELETE /api/memorias/{id}/foto` | Envia (ou troca), mostra e remove a foto; só o dono acessa |
| `/api/capitulos` e `/api/intencoes` | As mesmas cinco operações |
| `GET /api/estimativa` | Faixa estimada para o perfil (média brasileira até o questionário existir), com a curva de sobrevivência ano a ano |

Regras que a API garante:

- o aplicativo não escolhe `id` nem dono: campos desconhecidos são recusados;
- memória não pode ter data futura, nem texto vazio ou com mais de 280 caracteres;
- capítulo não pode terminar antes de começar;
- `veio_de` e `memoria_id` só aceitam memórias do próprio usuário;
- uma alteração parcial é validada junto com o resto do registro;
- registro excluído, inexistente ou de outra pessoa respondem igual: "não encontrado" (404).

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

A exportação e a importação valem só para a conta de quem está logado.

A importação casa os registros pelo `id`. Registro com o mesmo id é atualizado se o do arquivo for mais recente; nada é duplicado.
