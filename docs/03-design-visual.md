# 3. Design visual

O visual segue o protótipo. Este documento substitui as notas de estilo da especificação original (paleta terrosa, Merriweather), que foram abandonadas depois dos testes.

## Conceito

Fundo noturno com uma linha de luz. Cada capítulo é um fio luminoso, e a página ganha um brilho suave na cor do capítulo que está em tela. No futuro o brilho some e resta o fundo escuro.

O aplicativo tem só o tema escuro. Não há tema claro na v1.

## Cores de base

| Papel | Cor | Uso |
|---|---|---|
| Fundo | `#06070c` | Página |
| Superfície | `#0f111a` | Cartão "Hoje", diálogos, minimapa |
| Texto | `#f3f1ec` | Texto principal |
| Texto secundário | `#8b8ea3` | Etiquetas, datas, períodos vazios |
| Linha | `#262a3d` | Bordas e divisores |
| Destaque | `#ff5d73` → `#ffb65c` | Degradê usado só em "Hoje" e no botão principal |

## Cores de capítulo

O usuário escolhe a cor de cada capítulo nesta paleta fechada. Todas têm brilho parecido sobre o fundo escuro.

| Nome | Cor |
|---|---|
| Menta | `#5fe0b0` |
| Azul | `#5aa9ff` |
| Âmbar | `#ffc350` |
| Laranja | `#ff9a5a` |
| Rosa | `#ff6fb1` |
| Lavanda | `#a3a9cc` |
| Coral | `#ff5d73` |

## Regra da cor por época

Cada época tem uma cor só: a do **capítulo principal** daquele momento. Ela define:

- a borda luminosa das fotos;
- o círculo na linha;
- o pontinho da etiqueta de emoção;
- o brilho do fundo;
- a cor das semanas no minimapa.

Capítulos secundários sobrepostos aparecem apenas como fios paralelos na linha. A emoção de uma memória aparece como palavra, sem cor própria. Sem capítulo, usa-se o cinza do texto secundário.

## Tipografia

| Papel | Fonte | Uso |
|---|---|---|
| Títulos | Barlow Condensed, 500 e 600 | Anos, títulos de capítulo, "Hoje", etiquetas em maiúsculas espaçadas |
| Texto | Inter, 300 a 600 | Texto das memórias, parágrafos, formulários |

O texto das memórias nunca fica em maiúsculas nem em fonte condensada: ele precisa ser confortável de ler.

## Regras de estilo

- **Brilho com parcimônia.** Brilham a linha, os pontos, as bordas das fotos e o "Hoje". Texto comum não brilha.
- **Cantos pouco arredondados** (6 a 10 px) em fotos, cartões e diálogos; botões em formato de pílula.
- **Passado preenchido, futuro em contorno.** Anos futuros em contorno, intenções tracejadas.
- **Intensidade vira tamanho.** Memórias fortes têm texto e foto maiores e um ponto maior na linha.
- **Sem vermelho ou verde com sentido de certo e errado.** As cores identificam épocas, não julgam.
- **Movimento discreto.** Cartões entram suavemente ao rolar; nada pisca. Quem pede menos movimento no sistema operacional não vê animações.
- **Celular primeiro.** O layout de referência é o do celular: linha à esquerda, cartões em uma coluna, minimapa estreito. No computador, a linha vai para o centro e os cartões alternam de lado.
