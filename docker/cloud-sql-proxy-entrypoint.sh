#!/usr/bin/env bash
# Cloud SQL Auth Proxy をコンテナ内で起動してから、引数のコマンド (gunicorn や manage.py migrate) を実行する。
#
# - 環境変数 CLOUD_SQL_INSTANCE (例: project:asia-northeast1:aplus-mysql) が空なら、Proxy を使わずにコマンドだけ実行する。
# - Proxy は 127.0.0.1:${CLOUD_SQL_PROXY_PORT:-3306} で待ち受ける。DATABASE_URL はそこを指すこと。
# - コマンドが終わったら Proxy も止め、コマンドの終了コードで終わる (Cloud Run Jobs で使えるように)。
# - Proxy が先に落ちたら、コマンドも止めて失敗として終わる (Cloud Run にインスタンスを作り直させる)。
# - SIGTERM / SIGINT はコマンドに転送し、コマンドが終わるまで Proxy は動かしておく (処理中のリクエストが DB を使えるように)。
set -euo pipefail

if [[ $# -eq 0 ]]; then
  echo "usage: $0 command [args...]" >&2
  exit 2
fi

if [[ -z "${CLOUD_SQL_INSTANCE:-}" ]]; then
  exec "$@"
fi

proxy_port="${CLOUD_SQL_PROXY_PORT:-3306}"
startup_timeout="${CLOUD_SQL_PROXY_STARTUP_TIMEOUT:-30}"

cloud-sql-proxy \
  --address 127.0.0.1 \
  --port "${proxy_port}" \
  --structured-logs \
  "${CLOUD_SQL_INSTANCE}" &
proxy_pid=$!

# Proxy がポートを開くまで待つ
deadline=$((SECONDS + startup_timeout))
until (exec 3<>"/dev/tcp/127.0.0.1/${proxy_port}") 2>/dev/null; do
  if ! kill -0 "${proxy_pid}" 2>/dev/null; then
    wait "${proxy_pid}" || true
    echo "cloud-sql-proxy が起動中に終了しました" >&2
    exit 1
  fi
  if ((SECONDS >= deadline)); then
    echo "cloud-sql-proxy が ${startup_timeout} 秒以内に 127.0.0.1:${proxy_port} を開きませんでした" >&2
    kill -TERM "${proxy_pid}" 2>/dev/null || true
    wait "${proxy_pid}" || true
    exit 1
  fi
  sleep 0.2
done

"$@" &
app_pid=$!

forward_signal() {
  kill -TERM "${app_pid}" 2>/dev/null || true
}
trap forward_signal TERM INT

# コマンドか Proxy のどちらかが終わるまで待つ。
# wait -n は trap の実行中に子が終わると取りこぼして待ち続けることがある (bash 5.1) ので、1 秒ごとに生存を確かめる。
# sleep をバックグラウンドで wait するのは、シグナルを受けたらすぐ trap を動かすため。
set +e
while kill -0 "${app_pid}" 2>/dev/null && kill -0 "${proxy_pid}" 2>/dev/null; do
  sleep 1 &
  wait $!
done

if kill -0 "${app_pid}" 2>/dev/null; then
  wait "${proxy_pid}"
  echo "cloud-sql-proxy が終了しました (exit $?)。コマンドを止めます" >&2
  kill -TERM "${app_pid}" 2>/dev/null
  wait "${app_pid}"
  status=1
else
  wait "${app_pid}"
  status=$?
fi

trap - TERM INT
kill -TERM "${proxy_pid}" 2>/dev/null || true
wait "${proxy_pid}" 2>/dev/null
exit "${status}"
