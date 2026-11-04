![](https://www.aplus-tsukuba.net/static/board/new_logo.png)
# A_plus_Tsukuba  

<a href="https://www.buymeacoffee.com/halfblue" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" alt="Buy Me A Coffee" style="height: 60px !important;width: 217px !important;" ></a>

A+つくばは大学の課題を効率よく十分な品質で提出することができない (A+が取れない!!)問題を解決したい 同じ講義に知り合いが少ない筑波大生向けの筑波大生専用の匿名学習支援SNSです。

## サービスのURL
https://www.aplus-tsukuba.net/

## 概要
A+つくばは、筑波大学情報学群が開講する
「PBL形式によるネットワークサービス開発A (
[enPiT2](https://enpit.coins.tsukuba.ac.jp/))」において
チーム「半分、青い。」が開発していたプロジェクトで、
現在は[enpit2022](https://github.com/enpitut2022/A_plus_Tsukuba)のリポジトリよりforkし、
学生有志による私的なプロジェクトとして開発を行っています。

紹介動画：https://www.youtube.com/watch?v=dtbBatKRBvc

公式Twitter(現：X)：https://x.com/aplus_tsukuba

## 本番環境 (Cloud Run)
本番は Google Cloud の Cloud Run で動かし、DB は Cloud SQL for MySQL 8.4 を使います。
GCP 側の構成 (Cloud Run・Cloud SQL・Secret Manager・Cloud Build トリガーなど) は [half-blue/aplus-infra](https://github.com/half-blue/aplus-infra) の Terraform で管理しています。

- `main` ブランチに push すると、Cloud Build が [`cloudbuild.yaml`](cloudbuild.yaml) に従って次の順に実行します
  1. `Dockerfile` の `prod` ステージでイメージを作り、Artifact Registry に push する
  2. マイグレーション用の Cloud Run Job (`python manage.py migrate`) を新しいイメージで実行する
  3. Cloud Run サービスを新しいイメージでデプロイする
- 本番のイメージは gunicorn で動き、静的ファイルは WhiteNoise で配信します (`collectstatic` はビルド時に実行)
- DB へは、コンテナ内で起動する Cloud SQL Auth Proxy を経由して `127.0.0.1:3306` で接続します ([`docker/cloud-sql-proxy-entrypoint.sh`](docker/cloud-sql-proxy-entrypoint.sh))。
  MySQL 8.4 の既定の認証方式 (caching_sha2_password) が、Cloud Run 標準の Unix ソケット (`/cloudsql`) 経由では使えないためです
- 本番の設定は環境変数と Secret Manager から渡します (`SECRET_KEY`、`DATABASE_URL`、`ALLOWED_HOSTS` など)。`.env_local` は本番イメージには入りません

## マイグレーション
`board/migrations` をリポジトリで管理するようにしました (以前は `.gitignore` で除外していました)。
モデルを変えたら、`python manage.py makemigrations` で作ったファイルもコミットしてください。本番では Cloud Build がデプロイの前に `migrate` を実行します。

以前から手元の docker 環境を使っている場合は、手元の `board/migrations/0001_initial.py` などが `git pull` と衝突します。
次のどちらかで手元を揃えてください。

- 手元の DB を作り直す: 手元の `board/migrations/0*.py` を消してから `git pull` し、`docker compose down -v` で DB のボリュームを消して起動し直し、`python manage.py migrate` する
- 手元の DB を残す: 手元の `board/migrations/0*.py` を消してから `git pull` し、`python manage.py migrate --fake-initial` する
  (手元の DB のテーブルが今のモデルと同じ場合だけ使えます)

## ライセンス等
プロジェクトに含まれるファイルの内`kdb.json`は
[Make-IT-TSUKUBA](https://github.com/Make-IT-TSUKUBA)
さんが公開している[`kdb.json`](https://github.com/Make-IT-TSUKUBA/alternative-tsukuba-kdb/blob/master/src/kdb.json)をMPL-2.0 licenseのもとで利用しております。

## A+つくばとの連携について for Developers
A+つくばでは筑波大学に関連するアプリを開発している人に向けて連携機能を提供しています。詳しくは[こちら](https://github.com/half-blue/A_plus_Tsukuba/wiki/A-%E3%81%A4%E3%81%8F%E3%81%B0-for-Developers)をご確認ください。
