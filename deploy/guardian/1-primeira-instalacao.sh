# Vida em Semanas: primeira instalação no Pi, pelo Guardian.
# Colar em: site do Guardian > PC > Executar no Raspberry Pi (só o mestre). Tempo limite: 10 min.
# Roda como root, uma vez. Não sobe o sistema: deixa tudo pronto para a release/1 aparecer em Deploys.
# Passo a passo completo: docs/09-publicacao.md, seção "Com o Guardian".
set -euo pipefail

# ---------- preencha ----------
TAILNET="SUA-TAILNET.ts.net"         # o fim do endereço dos aparelhos, ex.: tail1234.ts.net
TS_AUTHKEY="tskey-auth-PREENCHA"     # chave do Tailscale com tag:semanas (pré-autorizada, uso único)
CHAVE_PUBLICA_AGE="age1PREENCHA"     # chave PÚBLICA das cópias (a privada fica fora do Pi)

# ---------- normalmente não precisa mudar ----------
NOME=vida-em-semanas
REPO=https://github.com/Allandpn/LifeJourney.git
WORKDIR=/opt/$NOME
SSD=/mnt/ssd
DADOS=$SSD/$NOME
COPIAS=/var/backups/$NOME
REGISTRO=/etc/guardian-deploy/projects.json
UID_APP=10001                        # usuário do servidor dentro do contêiner

falha() { echo "ERRO: $*"; exit 1; }

# 0. conferências antes de mudar qualquer coisa
[[ $TAILNET == *.ts.net && $TAILNET != SUA-* ]] || falha "preencha TAILNET"
[[ $TS_AUTHKEY == tskey-* && $TS_AUTHKEY != *PREENCHA* ]] || falha "preencha TS_AUTHKEY"
[[ $CHAVE_PUBLICA_AGE == age1* && $CHAVE_PUBLICA_AGE != *PREENCHA* ]] || falha "preencha CHAVE_PUBLICA_AGE"
mountpoint -q "$SSD" || falha "$SSD não está montado"
[ -f "$REGISTRO" ] || falha "não achei $REGISTRO"
[ -e "$WORKDIR" ] && falha "$WORKDIR já existe"
python3 -c 'import json,sys; sys.exit(1 if sys.argv[2] in json.load(open(sys.argv[1])) else 0)' "$REGISTRO" "$NOME" \
  || falha "o projeto $NOME já está no registro"

# 1. pasta de trabalho, só do root. Fica no primeiro commit do repositório: assim a release/1
#    é mais nova que "o que está no ar" e aparece em Deploys.
git clone --quiet "$REPO" "$WORKDIR"
git -C "$WORKDIR" checkout --quiet --detach "$(git -C "$WORKDIR" rev-list --max-parents=0 HEAD | tail -1)"
chown -R root:root "$WORKDIR"
chmod -R go-w "$WORKDIR"

# 2. dados (SSD) e cópias (cartão SD, outro dispositivo), só do usuário do contêiner
install -d -m 0700 -o "$UID_APP" -g "$UID_APP" "$DADOS" "$COPIAS"

# 3. configuração (.env), só do root
umask 077
cat > "$WORKDIR/.env" <<ENV
COMPOSE_PROFILES=tailscale
TS_HOSTNAME=$NOME
TS_AUTHKEY=$TS_AUTHKEY
TS_EXTRA_ARGS=--advertise-tags=tag:semanas
LJ_ORIGENS_PERMITIDAS=$NOME.$TAILNET
LJ_COPIA_CHAVE_PUBLICA=$CHAVE_PUBLICA_AGE
LJ_PASTA_DADOS=$DADOS
LJ_PASTA_COPIAS=$COPIAS
ENV

# 4. registro do deployer (com cópia do anterior)
cp -a "$REGISTRO" "$REGISTRO.antes-de-$NOME"
python3 - "$REGISTRO" "$NOME" "$WORKDIR" "$REPO" "$DADOS" "$COPIAS" <<'PY'
import json, os, sys
caminho, nome, workdir, repo, dados, copias = sys.argv[1:]
reg = json.load(open(caminho))
reg[nome] = {
    "repo": repo,
    "tag_prefix": "release/",
    "type": "compose",
    "workdir": workdir,
    "allowed_binds": [dados, copias],
    "sensitive": [
        "docker-compose*.yml", "Dockerfile", ".env*", "deploy/*",
        "servidor/app/seguranca.py", "servidor/app/api/contas.py", "servidor/app/api/admin.py",
        "servidor/app/api/dependencias.py", "servidor/app/repositorio.py", "servidor/app/principal.py",
        "servidor/app/config.py", "servidor/app/exportacao.py", "servidor/migracoes/*",
    ],
    "steps": [["docker", "compose", "up", "-d", "--build", "--remove-orphans"]],
    "health": [["sh", "-c", f"[ \"$(docker inspect -f '{{{{.State.Health.Status}}}}' {nome}-app-1)\" = healthy ]"]],
    "health_timeout_s": 300,
}
tmp = caminho + ".novo"
with open(tmp, "w") as f:
    json.dump(reg, f, ensure_ascii=False, indent=2)
os.chmod(tmp, 0o644)
os.replace(tmp, caminho)
PY

# 5. cópia de segurança toda noite, às 3h
cat > /etc/cron.d/$NOME <<CRON
0 3 * * * root cd $WORKDIR && docker compose exec -T app python -m app.copia fazer >> /var/log/$NOME-copia.log 2>&1
CRON
chmod 644 /etc/cron.d/$NOME

# 6. o deployer só lê o registro ao ligar: reinicia daqui a 20 s, fora deste script
systemd-run --quiet --on-active=20 --unit="$NOME-reinicia-deployer-$(date +%s)" systemctl restart guardian-deployer

echo "OK: $NOME cadastrado. Em cerca de 1 minuto, crie a etiqueta release/1 e ela aparece em Deploys."
echo "Registro anterior guardado em $REGISTRO.antes-de-$NOME"
