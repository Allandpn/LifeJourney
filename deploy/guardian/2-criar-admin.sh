# Vida em Semanas: cria a conta do administrador, depois do primeiro deploy.
# Colar em: site do Guardian > PC > Executar no Raspberry Pi (só o mestre). Tempo limite: 1 min.
# A saída (no histórico de Deploys) traz um link de uso único, válido por um dia, para criar a senha.
set -euo pipefail

EMAIL_ADMIN="voce@exemplo.com"   # preencha

[[ $EMAIL_ADMIN == *@* && $EMAIL_ADMIN != voce@exemplo.com ]] || { echo "ERRO: preencha EMAIL_ADMIN"; exit 1; }
cd /opt/vida-em-semanas
docker compose exec -T app python -m app.contas criar-admin "$EMAIL_ADMIN" --link
