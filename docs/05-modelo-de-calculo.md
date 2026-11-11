# 5. Modelo de cálculo

Resumo do embasamento científico. O sistema estima uma **faixa** de idade provável, a partir da mortalidade brasileira ajustada pelas respostas do questionário.

## Passos

Método de tábua de vida, o mesmo de Li et al. (2018).

1. **Base.** Idade atual exata `x0` e sexo selecionam as probabilidades anuais de morte `q_x` da tábua do IBGE.
2. **Risco combinado.** As respostas geram um `HR_total`. O valor 1,0 é o brasileiro médio de mesmo sexo e idade.
3. **Ajuste.** Cada `q_x` vira `q'_x`, de modo que nunca passe de 1:

   ```
   q'_x = 1 - (1 - q_x) ^ HR(x)
   ```

4. **Atenuação com a idade.** O efeito encolhe em idades avançadas:

   ```
   HR(x) = 1 + (HR_total - 1) * w(x)
   w(x) = 1 se x < 75;  (95 - x) / 20 entre 75 e 95;  0 acima de 95
   ```

5. **Sobrevivência** a partir de `x0`:

   ```
   S(x) = produto, de k = x0 até x-1, de (1 - q'_k)
   ```

6. **Saídas.**

   | Saída | Definição |
   |---|---|
   | Percentil 10 | Idade em que `S(x)` cai abaixo de 0,9 |
   | Mediana | Idade em que `S(x)` cai abaixo de 0,5 |
   | Percentil 90 | Idade em que `S(x)` cai abaixo de 0,1 |
   | Expectativa média | `x0 + soma de S(x)` |

O cálculo usa passos mensais, para a curva ficar suave. Um ano vale 52,1775 semanas.

## Combinação dos fatores

Multiplicar os riscos diretamente superestima o efeito, porque os fatores se sobrepõem.

1. **Recentrar na média brasileira.** A tábua já inclui fumantes, sedentários etc. Cada HR do usuário é dividido pela média daquele fator na população brasileira, ponderada pela prevalência de cada categoria.
2. **Bloco de marcadores.** Saúde autoavaliada, ritmo de caminhada e atividade física medem em boa parte a mesma coisa. Entram como um bloco: soma dos log-HRs recentrados vezes um redutor (provisório: 0,5).
3. **Teto e piso.** `HR_total` limitado a [0,4; 4,0].
4. **Pergunta pulada** conta como a média brasileira (HR recentrado 1,0).

```
HR_total = clamp(0,4 ; 4,0 ;
           produto_f (HR_f / média_BR_f) × exp(0,5 × soma_m log(HR_m / média_BR_m)))
```

## Fatores do questionário

| # | Fator | Natureza | "E se?" | Fonte |
|---|---|---|---|---|
| 1 | Tabagismo | Causal | Sim | Jha et al., NEJM 2013 |
| 2 | Peso (IMC) | Causal em parte | Sim | Global BMI Mortality Collaboration, Lancet 2016 |
| 3 | Álcool | Causal | Sim | Wood et al., Lancet 2018 |
| 4 | Atividade física | Causal e marcador | Sim | Ekelund et al., BMJ 2019 |
| 5 | Ritmo de caminhada | Marcador | Não | Zaccardi et al., Mayo Clin Proc 2019 |
| 6 | Saúde autoavaliada | Marcador | Não | DeSalvo et al., JGIM 2006 |
| 7 | Sono | Curto: causal provável | Só sono curto | Cappuccio et al., Sleep 2010 |
| 8 | Diabetes tipo 2 | Causal | Não | Emerging Risk Factors Collaboration, 2023 |
| 9 | Vínculos sociais | Causal provável | Sim | Holt-Lunstad et al., PLoS Med 2010 |
| 10 | Depressão | Causal incerto | Não | Cuijpers et al., Am J Psychiatry 2014 |

Só fatores causais e modificáveis recebem "e se?". Os valores de HR por resposta ficam no arquivo de configuração, com a fonte ao lado de cada número.

## Tábua do IBGE

- **Fonte:** Tábuas Completas de Mortalidade para o Brasil, 2024 (publicadas em 28/11/2025), planilhas `homens.xlsx` e `mulheres.xlsx` do [servidor de arquivos do IBGE](https://ftp.ibge.gov.br/Tabuas_Completas_de_Mortalidade/Tabuas_Completas_de_Mortalidade_2024/xlsx/).
- **No projeto:** `servidor/dados/tabua-ibge-2024.csv` (`idade, sexo, qx`), com as idades simples de 0 a 89. A ferramenta `servidor/ferramentas/converter_tabua_ibge.py` converte as planilhas de qualquer ano.
- **Acima de 89 anos:** a tábua termina no grupo aberto "90 ou mais". A partir dele, o risco segue uma curva de Gompertz que parte do risco publicado aos 89 e sobe com a inclinação que reproduz a expectativa publicada para o grupo aberto (4,57 anos para homens e 5,32 para mulheres). A Gompertz ajustada só às idades de 60 a 89 servia para os homens, mas fazia as mulheres morrerem rápido demais depois dos 90.
- **Validação** (testes automáticos, margem de 0,02 ano):

  | | Homens: modelo | Homens: IBGE | Mulheres: modelo | Mulheres: IBGE |
  |---|---|---|---|---|
  | Ao nascer | 73,31 | 73,31 | 79,87 | 79,87 |
  | Aos 60 | 20,80 | 20,80 | 24,15 | 24,15 |
  | Aos 90 | 4,57 | 4,57 | 5,32 | 5,32 |

- **Corcova dos homens jovens:** entre 28 e 31 anos, a mortalidade masculina cai um pouco antes de voltar a subir. É o excesso de mortes por violência e acidentes. A curva provisória do briefing era lisa e não tinha isso; por isso o percentil 10 dos homens jovens ficou mais baixo com a tábua real.
- **Ano que vem:** o IBGE publica a tábua de 2025 até 1º/12/2026. Basta converter as planilhas, trocar o arquivo e as expectativas de referência em `fatores.json`, e rodar os testes.
- **Limitação:** é tábua de período, não de coorte; para quem é jovem hoje, subestima levemente a vida.

### O que mudou com a tábua real

Homem de 38,4 anos (o caso de teste do briefing):

| | Curva provisória | Tábua real |
|---|---|---|
| Brasileiro médio: média / P10 / mediana / P90 | 77,7 / 59,2 / 79,6 / 92,9 | 77,1 / 57,4 / 79,4 / 92,9 |
| Caso de teste (risco 1,65) | 72,8 / 54,4 / 74,0 / 88,7 | 72,0 / 52,6 / 73,3 / 88,6 |
| "E se?" vínculos / sono / atividade / IMC / todas | +211 / +61 / +49 / +36 / +338 semanas | +221 / +64 / +51 / +38 / +354 semanas |

A diferença maior está no P10 (quase 2 anos): a tábua real tem mais mortes entre os 30 e os 60 anos do que a curva lisa, sobretudo por causas externas. A mediana e o P90 quase não mudam.

## Tudo em configuração

Nenhum número do modelo fica espalhado no código. O arquivo [`servidor/dados/fatores.json`](../servidor/dados/fatores.json) guarda:

- os HRs de cada resposta e a fonte;
- as prevalências brasileiras de cada categoria e a fonte;
- os parâmetros provisórios: idades da atenuação (75 e 95), redutor dos marcadores (0,5), teto e piso (4,0 e 0,4);
- o caminho da tábua.

Cada resposta tem um `status` que diz o grau de confiança do número:

| Status | Significado |
|---|---|
| `publicado` | Aparece no resumo do artigo |
| `aproximado` | Derivado, ou precisa ser conferido no texto completo |
| `provisorio` | Sem fonte direta; serve só para testar o sistema |

A média brasileira de cada fator pode ser dada direto (`valor`) ou calculada das prevalências de cada resposta (`prevalencias`), que é a forma definitiva.

Respostas publicadas em anos de vida, e não em HR (álcool), são escritas como `perda_anos` e convertidas em HR pelo próprio núcleo, usando a tábua ativa.

## Implementação

O núcleo fica em [`servidor/app/nucleo/`](../servidor/app/nucleo/):

| Arquivo | Faz |
|---|---|
| `tabua.py` | Tábua provisória de Gompertz-Makeham, leitura do CSV do IBGE e extensão acima de 80 anos |
| `fatores.py` | Recentragem, bloco de marcadores, teto e piso, faixas de IMC |
| `sobrevivencia.py` | Atenuação com a idade, curva de sobrevivência, percentis e expectativa |
| `modelo.py` | Junta tudo; conversão de anos perdidos em HR; "e se?" |

A curva usa passos mensais. Dentro de cada ano de idade, o risco instantâneo é constante (`mu = -ln(1 - q_x)`), o que equivale à fórmula `q'_x = 1 - (1 - q_x)^HR`.

O ganho de cada "e se?" é a diferença na expectativa média, convertida em semanas.

## Situação em novembro de 2026

Com a tábua provisória, o núcleo reproduz o protótipo descrito no briefing: diferenças de até 0,1 ano nos percentis e de 1 semana nos ganhos do "e se?".

Com a tábua real, a calibração bate para as mulheres e ainda não para os homens. Aos 50 anos, o perfil com quatro hábitos saudáveis vive 15,3 anos (mulheres) e 16,9 anos (homens) a mais que o perfil sem nenhum, contra 14 e 12 em Li et al. O perfil sem hábitos bate no teto de 4,0. O caso dos homens está marcado como falha esperada em `test_calibracao.py`.

O teto também achata o "e se?" de perfis com muitos fatores de risco: se o risco total passaria de 4,0, tirar um fator pequeno quase não muda o risco já cortado no teto. Num perfil de teste com risco de 4,4 (cortado para 4,0), dormir de 6 a 8 horas rendeu só 9 semanas. A calibração do teto deve levar isso em conta.

Como as médias brasileiras ainda são placeholders, um perfil com alguns fatores de risco pode sair com risco total abaixo de 1,0. Isso é efeito da recentragem sobre médias inventadas, e muda quando as prevalências reais entrarem.

## Pendências científicas

Podem andar em paralelo ao código.

- [x] Importar a tábua real do IBGE 2024 e estender acima do grupo aberto (90 anos).
- [ ] Conferir no texto completo dos artigos os HRs derivados ou aproximados.
- [ ] Converter álcool e ritmo de caminhada de "anos de vida" para HR.
- [ ] Definir um HR mais modesto para atividade física autorreferida.
- [ ] Levantar as prevalências brasileiras reais (Vigitel, PNS). As usadas até agora são provisórias, sem fonte.
- [ ] Escolher a forma final da atenuação depois dos 75 anos.
- [ ] Calibrar redutor, teto e piso contra Li et al. (2018): perfil com cinco hábitos saudáveis contra nenhum, aos 50 anos, deve dar perto de 12 anos de diferença (homens) e 14 (mulheres).

## Como o cálculo aparece na interface

- Na linha do tempo, só como forma do futuro: onde a linha fica tracejada e o quanto esmaece.
- No minimapa, como o esmaecimento das semanas futuras.
- Na tela "Estimativa", aberta pelo cartão "Hoje" ("Como o futuro é estimado") ou pelos marcos do futuro: a faixa em anos, a mediana, as semanas até o meio da faixa, o ganho em semanas de cada "e se?" e o histórico. A tela sempre lembra que não é aconselhamento médico e que os números ainda são provisórios.

O cálculo nunca aparece como contagem regressiva.
