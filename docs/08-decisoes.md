# 8. Decisões

Registro curto do que foi decidido e do que falta decidir. Decisões tomadas não se reabrem sem motivo.

## Decididas

| Decisão | Motivo |
|---|---|
| Celular como uso principal | É onde o usuário vai registrar e rever |
| Login e sincronização entre aparelhos | Usar no celular e no computador com os mesmos dados |
| Várias pessoas, cada uma com a própria conta, isoladas entre si | Outras pessoas poderão usar, com segurança e privacidade |
| Hospedagem em um Raspberry Pi 4 ligado 24 horas | Já existe e roda outros projetos pessoais |
| Python no núcleo de cálculo e no servidor | Preferência do projeto |
| Linha do tempo rolável no lugar da grade como tela principal | A grade mostra quantidade de tempo; a rolagem mostra o conteúdo dele |
| A grade de semanas continua como minimapa | Mantém a visão da vida inteira num relance e dá lugar à estimativa |
| Passado acima, futuro abaixo | O futuro "à frente" combina com planejar |
| Granularidade ano / mês / semana | Zoom progressivo |
| Visual noturno com linha luminosa e fonte condensada | Escolha feita sobre o protótipo; substitui a paleta terrosa |
| Uma cor por época, a do capítulo principal | Evita excesso de cores |
| Sem tema claro na v1 | O visual foi pensado para o escuro |
| Sem insígnias, rede social ou IA | Contrariam os princípios do projeto |
| Repositório público; dados reais e segredos fora do git | Privacidade |

## Decisões revistas

| Antes | Agora | Consequência |
|---|---|---|
| 100% local, sem conta e sem servidor | Servidor próprio com login | Memórias e respostas de saúde passam a ficar em um servidor. Exige hospedagem, HTTPS e cuidado com senhas. A exportação em formato aberto continua |
| TypeScript em tudo | Python no servidor e no cálculo; TypeScript só na tela | Duas linguagens no projeto |

| Até a etapa 5, um usuário de desenvolvimento, só em modo desenvolvimento | Permite testar a API antes do login; em produção o servidor recusa tudo |
| Exclusão por marcação (`excluido_em`) | Outros aparelhos ficam sabendo da exclusão |
| Fotos regravadas em JPEG de até 1600 px, sem metadados | Economiza espaço no Raspberry Pi e remove o local GPS e o modelo do celular |
| Excluir pede um segundo toque, sem janela de confirmação | Evita exclusão por engano sem interromper |
| Alembic para mudanças no banco, antes da etapa 7 | Até lá, mudar uma tabela é apagar o banco de desenvolvimento |

## Propostas, aguardando confirmação

| Proposta | Alternativa |
|---|---|
| Servidor com FastAPI, SQLModel e SQLite | Serviço pronto de login e banco (por exemplo Supabase), com Python só no cálculo |
| Aplicativo web instalável (PWA) em TypeScript, sem framework | Aplicativo nativo para Android |
| Sincronização direta na v1: precisa de internet para registrar | Registrar sem conexão e enviar depois (mais complexo) |
| Contas criadas por link de convite | Cadastro aberto a qualquer pessoa |
| Docker Compose no Raspberry Pi | Rodar direto no sistema, como serviço |
| Cloudflare Tunnel para acesso externo, com domínio próprio | Abrir porta no roteador com Caddy e DNS dinâmico; ou Tailscale, só para aparelhos autorizados |
| Banco e fotos em SSD externo cifrado, com cópia noturna cifrada para fora do Pi | Cartão SD, sem cópia |
| Na v1, o administrador pode tecnicamente abrir o banco; a tela de cadastro avisa | Cifrar os dados com a senha de cada usuário (v2) |
| Redefinição de senha por link gerado pelo administrador | Envio de e-mail |
| O passado é o centro; a estimativa só dá forma ao futuro | Estimativa em destaque na tela principal |
| Emoção e intensidade entram na v1 | Deixar para depois |
| Campo `principal` no capítulo define a cor da época | Usar sempre o capítulo mais antigo em andamento |
| Marcadores de texto discretos na faixa estimada | Só o esmaecimento, sem texto |
| Revisão periódica de fase fica para depois da v1 | Incluir na v1 |

## Em aberto

| Pergunta | Impacto |
|---|---|
| Como os outros projetos rodam no Pi hoje (Docker, serviços)? | Define como este se encaixa sem conflito de portas |
| Já existe um domínio próprio? | Necessário para o Cloudflare Tunnel |
| Para onde vai a cópia de segurança? | Outro disco em casa ou armazenamento em nuvem |
| Por quanto tempo as cópias de segurança são mantidas? | Prazo para os dados de uma conta apagada sumirem de vez |
| Limite de 280 caracteres por memória é suficiente? | Modelo de dados e layout dos cartões |
| Como o usuário escolhe "veio de" ao criar uma memória? | Desenho da tela de edição |
| O grid do minimapa vai até que idade? | Hoje vai um pouco além do percentil 90 |
