# Dockerfile for A_plus_tsukuba service container
#
# ステージ
#   dev  : ローカル開発用 (docker-compose.yml が target: dev で使う)。ソースは volume で同期する
#   prod : 本番 (Cloud Run) 用。最後のステージなので、target を指定しないビルドはこれになる

# Python version is same as the production.
ARG PYTHON_VERSION=3.8.20

# ---------------------------------------------------------------------------
# dev
# ---------------------------------------------------------------------------
# Download python image
FROM python:${PYTHON_VERSION}-bullseye AS dev

# Cast a spell
ENV PYTHONUNBUFFERED 1

# MySQL Connector
RUN apt-get update
RUN apt-get -y install default-mysql-client

RUN mkdir /a_plus_tsukuba

# Install poerty
RUN pip install poetry==1.8.2
RUN poetry config virtualenvs.create false

# Set working dir
WORKDIR /a_plus_tsukuba

# Copy poetry files
COPY ./pyproject.toml* ./poetry.lock* ./

# Install Dependencies
RUN poetry install --no-root
# Cast a spell "--no-root" cf. https://github.com/python-poetry/poetry/issues/689

# Copy .env for local
COPY ./.env_local ./.env

# Copy files
COPY ./manage.py ./
COPY ./pytest.ini ./

# NOTICE
# ./A_plus_Tsukuba and ./board are synchronized by volume configs in docker-compose.yml

# ---------------------------------------------------------------------------
# prod: 依存パッケージのビルド
# ---------------------------------------------------------------------------
FROM python:${PYTHON_VERSION}-bullseye AS builder

RUN pip install --no-cache-dir poetry==1.8.2

WORKDIR /build
COPY ./pyproject.toml ./poetry.lock ./

# 本番に要る依存 (main グループ) だけを /install に入れる。
# mysqlclient はここで libmariadb-dev (bullseye 同梱) を使ってビルドされる。
RUN poetry export --only main --format requirements.txt --output requirements.txt \
    && pip install --no-cache-dir --prefix=/install -r requirements.txt

# ---------------------------------------------------------------------------
# prod: Cloud SQL Auth Proxy
# ---------------------------------------------------------------------------
# MySQL 8.4 の caching_sha2_password は Auth Proxy の Unix ソケット経由では使えないので、
# Cloud Run 標準の /cloudsql ソケットではなく、コンテナ内で Proxy を TCP で動かす。
FROM gcr.io/cloud-sql-connectors/cloud-sql-proxy:2.27.0 AS cloud-sql-proxy

# ---------------------------------------------------------------------------
# prod
# ---------------------------------------------------------------------------
FROM python:${PYTHON_VERSION}-slim-bullseye AS prod

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8080

# mysqlclient の実行時ライブラリ (caching_sha2_password のクライアントプラグインを含む)
RUN apt-get update \
    && apt-get install -y --no-install-recommends libmariadb3 \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /install /usr/local
COPY --from=cloud-sql-proxy /cloud-sql-proxy /usr/local/bin/cloud-sql-proxy
COPY ./docker/cloud-sql-proxy-entrypoint.sh /usr/local/bin/cloud-sql-proxy-entrypoint

WORKDIR /a_plus_tsukuba

COPY ./manage.py ./
COPY ./A_plus_Tsukuba ./A_plus_Tsukuba
COPY ./board ./board

# 静的ファイルを集める。settings.py が必須とする環境変数には、ビルド用のダミー値を渡す (イメージには残らない)。
RUN SECRET_KEY=collectstatic-only DEBUG=False ALLOWED_HOSTS=localhost DATABASE_URL=sqlite:////tmp/collectstatic.sqlite3 \
    python manage.py collectstatic --noinput

RUN useradd --system --no-create-home --uid 10001 app
USER app

# CLOUD_SQL_INSTANCE が設定されていれば、Cloud SQL Auth Proxy を起動してからコマンドを実行する
ENTRYPOINT ["/usr/local/bin/cloud-sql-proxy-entrypoint"]
# 1 vCPU に 1 ワーカー、スレッドで並列に捌く (Cloud Run の推奨構成)。タイムアウトは Cloud Run 側に任せる
CMD ["sh", "-c", "exec gunicorn --bind :${PORT} --workers 1 --threads 8 --timeout 0 A_plus_Tsukuba.wsgi:application"]
