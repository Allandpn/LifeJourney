# 2. Experiência

A referência viva deste documento é o protótipo em [`prototipo/linha-do-tempo.html`](../prototipo/linha-do-tempo.html).

## A linha do tempo

A tela principal é uma linha vertical contínua. O passado fica acima, o futuro abaixo, e o aplicativo sempre abre em "Hoje".

| Elemento | Comportamento |
|---|---|
| Linha central | Um fio luminoso por capítulo. Capítulos sobrepostos correm lado a lado. |
| Abertura de capítulo | Título grande e período, na cor do capítulo. |
| Memória | Cartão preso à linha, alternando de lado. Com foto, mostra a foto; sem foto, só o texto. |
| Ponto na linha | Um círculo por período com memórias. O tamanho segue a memória mais intensa. |
| Período vazio | Vários períodos sem registro viram uma única faixa fina, com o convite "lembrar de algo". |
| Contexto fixo | O topo mostra o ano, a idade e os capítulos do trecho em tela. |
| Botão "Hoje" | Sempre visível; volta ao presente. |

A rolagem tem começo (o nascimento) e um fim suave, pouco depois do percentil 90 da estimativa.

## Granularidade

O usuário escolhe o nível de detalhe. Trocar de nível mantém o ponto da linha em que ele estava.

| Nível | Cada linha é | O que mostra |
|---|---|---|
| Ano | um ano do calendário | até 3 memórias (as marcantes e mais intensas primeiro) e um link para as demais |
| Mês | um mês | todas as memórias do mês |
| Semana | uma semana de vida | o conteúdo completo; as 3 semanas mais recentes aparecem mesmo vazias |

## Hoje

O dia de hoje tem uma linha própria, com:

- o número da semana de vida e a idade;
- os capítulos em andamento;
- "nesta semana, em outros anos": memórias de datas próximas em anos anteriores;
- um botão para registrar algo de hoje.

Uma memória marcada como "não me lembrar disto" nunca aparece em "nesta semana, em outros anos". Ela continua na linha.

## Futuro

- Os anos aparecem só em contorno, sem preenchimento.
- Intenções têm contorno tracejado e nunca são preenchidas como memórias.
- Intenções com intervalo vago aparecem no meio do intervalo ("entre 2027 e 2028").
- Intenções "algum dia" ficam juntas, num bloco sem data.
- A linha é contínua até o percentil 10 da estimativa, tracejada e cada vez mais tênue até o percentil 90, e quase apagada depois.
- Três marcadores discretos de texto indicam o início da faixa, o meio e o fim. Nenhum fala em morte ou em tempo restante.

Sem questionário respondido, o futuro usa a curva do brasileiro médio de mesmo sexo e idade.

## Minimapa

Uma faixa fixa na lateral mostra a vida inteira como grade de semanas (52 colunas por ano de idade).

- Semanas vividas têm a cor do capítulo principal da época.
- Semanas com memória aparecem em destaque.
- Semanas futuras esmaecem conforme a estimativa.
- Um retângulo marca o trecho que está na tela.
- Tocar ou arrastar leva a rolagem para aquele período.

## Telas

| Tela | Conteúdo |
|---|---|
| Primeiro acesso | Pede só a data de nascimento e o sexo. A linha aparece na hora, vazia. Convite opcional para registrar de 3 a 5 memórias marcantes. |
| Linha do tempo | A tela principal, descrita acima. |
| Detalhe da memória | Foto, texto, data, idade, semana, capítulo, emoção, ligações "veio de / levou a", silenciar. |
| Criar ou editar memória | Texto, data (padrão hoje, aceita o passado), foto, emoção, intensidade, marcante, "veio de". |
| Criar ou editar capítulo | Nome, início, fim opcional, cor, categoria, notas, se é capítulo principal. |
| Criar ou editar intenção | Nome, horizonte (data, intervalo ou "algum dia"), status, notas. |
| Questionário e "e se?" | Perguntas de saúde, faixa resultante e ganho de cada mudança de hábito. Tela separada e opcional. |
| Backup | Onde os dados ficam, exportar, importar e a data do último backup. |

## Tom dos textos

Direto e calmo. Convites em vez de cobranças ("lembrar de algo", não "você ainda não registrou"). Sem linguagem ornamentada.
