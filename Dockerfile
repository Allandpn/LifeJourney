# Imagem do Vida em Semanas: o aplicativo compilado e o servidor Python numa só.
# Funciona no Raspberry Pi (ARM 64 bits) e em computadores comuns.

# ---------- 1. compila o aplicativo ----------
FROM node:22-bookworm-slim AS aplicativo
WORKDIR /aplicativo
COPY aplicativo/package.json aplicativo/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY aplicativo/ ./
RUN npm test && npm run build

# ---------- 2. servidor ----------
FROM python:3.12-slim-bookworm
# age: cifra as cópias de segurança
RUN apt-get update \
    && apt-get install -y --no-install-recommends age \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /servico/servidor
COPY servidor/pyproject.toml ./
COPY servidor/app ./app
COPY servidor/dados ./dados
COPY servidor/migracoes ./migracoes
COPY servidor/alembic.ini ./
RUN pip install --no-cache-dir .
COPY --from=aplicativo /aplicativo/dist /servico/aplicativo
# o código precisa ser legível pelo usuário que roda o servidor, qualquer que seja a
# permissão com que os arquivos chegaram (o git normaliza, mas uma cópia direta não)
RUN chmod -R a+rX /servico

# roda sem ser root; os dados ficam no volume /dados, as cópias em /copias
# uid 10001 (como o gateway do Guardian): não coincide com o usuário comum do Pi (1000),
# que assim não consegue ler o banco e as fotos
RUN useradd --create-home --uid 10001 vida && mkdir -p /dados /copias && chown vida:vida /dados /copias
USER vida

ENV LJ_MODO=producao \
    LJ_BANCO=/dados/lifejourney.db \
    LJ_FOTOS=/dados/fotos \
    LJ_COPIAS=/copias \
    LJ_APLICATIVO=/servico/aplicativo \
    PYTHONUNBUFFERED=1

EXPOSE 8000
HEALTHCHECK --interval=60s --timeout=5s --start-period=20s \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/saude', timeout=4)"
CMD ["uvicorn", "app.principal:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
