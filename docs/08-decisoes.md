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

| Contas criadas por link de convite | Sem cadastro aberto num servidor exposto à internet |
| Redefinição de senha por link gerado pelo administrador | A v1 não envia e-mails |
| Sessão em cookie, com o código guardado só como hash no servidor | Permite listar e desconectar aparelhos; o JavaScript não lê o cookie |
| Exclusão por marcação (`excluido_em`) | Outros aparelhos ficam sabendo da exclusão |
| Fotos regravadas em JPEG de até 1600 px, sem metadados | Economiza espaço no Raspberry Pi e remove o local GPS e o modelo do celular |
| Excluir pede um segundo toque, sem janela de confirmação | Evita exclusão por engano sem interromper |
| Alembic para mudanças no banco, antes da etapa 7 | Até lá, mudar uma tabela é apagar o banco de desenvolvimento |

| Docker Compose no Raspberry Pi, sem portas abertas | Isola dos outros projetos do Pi; acesso só pelo túnel |
| Cloudflare Tunnel para acesso externo | HTTPS automático sem abrir o roteador; Tailscale documentado como alternativa, sem teste |
| Cópias cifradas com chave pública (`age`), chave privada fora do Pi | Quem levar o Pi ou o disco de cópias não lê nada |
| Migrações do banco com Alembic, aplicadas ao ligar | Mudanças nas tabelas sem perder dados reais |
| Sem modo sem conexão na v1 | Não deixar memórias e respostas de saúde guardadas num celular que pode ser perdido |

## Propostas, aguardando confirmação

| Proposta | Alternativa |
|---|---|
| Servidor com FastAPI, SQLModel e SQLite | Serviço pronto de login e banco (por exemplo Supabase), com Python só no cálculo |
| Aplicativo web instalável (PWA) em TypeScript, sem framework | Aplicativo nativo para Android |
| Banco e fotos em SSD externo cifrado com LUKS | Cartão SD sem cifra |
| Na v1, o administrador pode tecnicamente abrir o banco; a tela de cadastro avisa | Cifrar os dados com a senha de cada usuário (v2) |
| O passado é o centro; a estimativa só dá forma ao futuro | Estimativa em destaque na tela principal |
| Emoção e intensidade entram na v1 | Deixar para depois |
| Campo `principal` no capítulo define a cor da época | Usar sempre o capítulo mais antigo em andamento |
| Marcadores de texto discretos na faixa estimada | Só o esmaecimento, sem texto |
| Revisão periódica de fase fica para depois da v1 | Incluir na v1 |

## Em aberto

| Pergunta | Impacto |
|---|---|
| Já existe um domínio próprio? | Sem ele, usar a alternativa do Tailscale (docs/09-publicacao.md) |
| Para onde vai a cópia de segurança? | Pasta configurável (`LJ_PASTA_COPIAS`); pode ser outro disco e, por estar cifrada, também a nuvem |
| Por quanto tempo as cópias de segurança são mantidas? | Hoje, as 30 mais recentes (`LJ_COPIA_MANTER`). Define o prazo para os dados de uma conta apagada sumirem de vez |
| Limite de 280 caracteres por memória é suficiente? | Modelo de dados e layout dos cartões |
| Como o usuário escolhe "veio de" ao criar uma memória? | Desenho da tela de edição |
| O grid do minimapa vai até que idade? | Hoje vai um pouco além do percentil 90 |
