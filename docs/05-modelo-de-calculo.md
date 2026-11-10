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

- **Fonte:** Tábuas Completas de Mortalidade para o Brasil, 2024 (publicadas em 28/11/2025).
- **Formato no projeto:** um CSV simples (`idade, sexo, qx`), trocável sem mudar código quando sair a edição seguinte.
- **Acima de 80 anos:** a tábua termina num grupo aberto. Ajusta-se uma curva de Gompertz às idades de 60 a 80 e extrapola-se até 110 ou 120.
- **Validação da importação:** expectativa ao nascer 76,6 anos (homens 73,3; mulheres 79,9); aos 60 anos, mais 20,8 (homens) e 24,2 (mulheres).
- **Limitação:** é tábua de período, não de coorte; para quem é jovem hoje, subestima levemente a vida.

## Tudo em configuração

Nenhum número do modelo fica espalhado no código. Um arquivo de configuração guarda:

- os HRs de cada resposta e a fonte;
- as prevalências brasileiras de cada categoria e a fonte;
- os parâmetros provisórios: idades da atenuação (75 e 95), redutor dos marcadores (0,5), teto e piso (4,0 e 0,4);
- o caminho da tábua.

## Pendências científicas

Podem andar em paralelo ao código.

- [ ] Importar a tábua real do IBGE 2024 e estender acima de 80 anos.
- [ ] Conferir no texto completo dos artigos os HRs derivados ou aproximados.
- [ ] Converter álcool e ritmo de caminhada de "anos de vida" para HR.
- [ ] Definir um HR mais modesto para atividade física autorreferida.
- [ ] Levantar as prevalências brasileiras reais (Vigitel, PNS). As usadas até agora são provisórias, sem fonte.
- [ ] Escolher a forma final da atenuação depois dos 75 anos.
- [ ] Calibrar redutor, teto e piso contra Li et al. (2018): perfil com cinco hábitos saudáveis contra nenhum, aos 50 anos, deve dar perto de 12 anos de diferença (homens) e 14 (mulheres).

## Como o cálculo aparece na interface

- Na linha do tempo, só como forma do futuro: onde a linha fica tracejada e o quanto esmaece.
- No minimapa, como o esmaecimento das semanas futuras.
- Na tela do questionário, como a faixa em anos e o ganho em semanas de cada "e se?".

O cálculo nunca aparece como contagem regressiva.
