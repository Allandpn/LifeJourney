# 1. Visão

## O que é

Um aplicativo de uso pessoal, pensado primeiro para o celular, que mostra a vida inteira como uma linha do tempo vertical. O usuário rola por ela e vê os marcos de cada período, com fotos e textos curtos.

O sistema tem três objetivos, um para cada parte do tempo:

| Parte | Objetivo | Como aparece |
|---|---|---|
| Passado | Prazer em rever a própria trajetória | Memórias e capítulos, com fotos e texto |
| Presente | Apreciação da semana atual | Cartão "Hoje" e "nesta semana, em outros anos" |
| Futuro | Planejamento sem cobrança | Intenções com horizonte flexível, sobre uma faixa estimada de vida |

## Para quem

Pessoas que querem rever e planejar a própria vida, usando principalmente o celular e às vezes o computador. Cada pessoa tem a própria conta e vê os mesmos dados em todos os seus aparelhos.

As contas são totalmente separadas: ninguém vê nada de outra pessoa. Não há rede social nem compartilhamento.

## O que o diferencia

Os aplicativos parecidos se dividem em dois grupos: diários em linha do tempo (como o Lifeline) e grades de semanas com contagem regressiva (como o Life Atlas). Este projeto junta quatro coisas que eles não oferecem em conjunto:

1. **Estimativa com base científica.** A faixa de vida vem da tábua do IBGE ajustada por um questionário com riscos relativos publicados. É sempre uma faixa, nunca uma data.
2. **"E se?" por hábito.** Mostra quantas semanas cada hábito modificável acrescenta.
3. **Capítulos e ligações entre eventos.** Uma memória pode apontar para a que a causou ("veio de" / "levou a"), o que transforma a lista em trajetória.
4. **Intenções sem prazo rígido.** O horizonte pode ser uma data, um intervalo vago ou "algum dia".

## Princípios

Valem para toda decisão de design e de código.

1. **O passado é o centro.** A estimativa de vida só dá forma ao futuro; ela não é o assunto principal da tela.
2. **Faixa, nunca data.** O futuro esmaece aos poucos e não tem ponto final.
3. **Sem culpa e sem gamificação.** Nada de insígnias, sequências, barras de progresso ou status "concluído / não concluído".
4. **Fases difíceis têm o mesmo peso que conquistas.** O sistema não força tom positivo.
5. **Toda pergunta do questionário precisa de um número publicado.** Só entra o que tiver risco relativo de mortalidade vindo de meta-análise ou coorte grande.
6. **Conservador.** Na dúvida entre dois efeitos, usa-se o menor; o ajuste total tem teto e piso.
7. **Os dados são de cada usuário.** Ficam em um servidor próprio, atrás de login, isolados por conta, e nunca são compartilhados com terceiros. Cada pessoa pode exportar tudo em formato aberto e apagar a própria conta quando quiser.
8. **Não é aconselhamento médico.** O "e se?" mostra ganhos, nunca perdas, e fica fora da tela principal.
9. **Sem obrigação diária.** O usuário registra quando algo importa e pode preencher o passado aos poucos.

## Escopo da v1

### Dentro

- Contas individuais, criadas por convite, com login e sincronização entre aparelhos.
- Data de nascimento e sexo.
- Linha do tempo rolável com granularidade ano / mês / semana.
- Memórias com texto, foto, emoção e intensidade.
- Capítulos, inclusive sobrepostos.
- Intenções com horizonte flexível.
- Ligação "veio de / levou a" entre memórias.
- Minimapa da vida em semanas.
- "Nesta semana, em outros anos", com a opção de silenciar uma memória.
- Questionário de saúde, faixa estimada (percentis 10, 50 e 90) e "e se?".
- Backup por exportação e importação.
- Instalação no celular como aplicativo (PWA).

### Fora

- Cadastro aberto a qualquer pessoa (as contas são criadas por convite).
- Recuperação de senha por e-mail (na v1 o administrador gera um link de redefinição).
- Registrar memórias sem conexão (na v1, sem internet o aplicativo só mostra o que já foi carregado).
- Componente social.
- Recursos de IA.
- Vídeo, áudio e música nas memórias.
- Senha por memória e criptografia (candidato a v2).
- Ajuste regional, dieta, renda, histórico familiar no cálculo.
- Incerteza dos próprios riscos relativos (candidato a v2).
- Revisão periódica de fase com notificações (candidato a v2; na v1 o capítulo é fechado manualmente).
