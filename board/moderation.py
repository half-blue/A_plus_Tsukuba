"""新着の投稿・返信・レビューを、モデレーション用の Discord のチャンネルに Webhook で知らせる。

- 送り先は設定 DISCORD_MODERATION_WEBHOOK_URL (環境変数)。未設定なら何もしない (ローカルの開発環境やテスト)。
- 保存したリクエストの中で、そのまま (同期的に) 送る。レスポンスを返したあとに裏のスレッドで送ると、
  リクエストのあいだしか CPU を割り当てない実行環境 (Cloud Run など) では送り終わる保証がないため。
- 送れなくても投稿は成功させ、警告のログだけを残す。送り直しはしない。
"""

import json
import logging
import urllib.request

from django.conf import settings
from django.urls import reverse

logger = logging.getLogger(__name__)

# Discord のメッセージ (content) の上限の文字数
MAX_CONTENT_LENGTH = 2000

# 送信のタイムアウト (秒)。投稿のレスポンスはこの分だけ遅れうる
TIMEOUT_SECONDS = 3

# Discord の前段 (Cloudflare) は urllib の既定の User-Agent を拒むので、自分の名前を付ける
USER_AGENT = "aplus-tsukuba-moderation/1.0"

TRUNCATED_MARK = "…(省略)"


def is_enabled():
    return bool(settings.DISCORD_MODERATION_WEBHOOK_URL)


def post_message(post):
    footer = [_admin_line("post", post.pk)]
    if post.allow_tweet:
        footer.append("**X への自動投稿が有効な投稿です。この投稿を消すときは、X のポストも消してください。**")
    return _build(
        header=[f"[Post: {post.pk}]", f"Sender: {_inline(post.sender_name)}"],
        body=post.text,
        footer=footer,
    )


def reply_message(reply):
    return _build(
        header=[f"[Reply: {reply.pk}]", f"Sender: {_inline(reply.sender_name)}"],
        body=reply.text,
        footer=[_admin_line("reply", reply.pk)],
    )


def review_message(review):
    return _build(
        header=[f"[Review: {review.pk}]"],
        body=review.comment,
        footer=[_admin_line("review", review.pk)],
    )


def send(content):
    """content を Webhook に送る。失敗しても例外は出さない。"""
    url = settings.DISCORD_MODERATION_WEBHOOK_URL
    if not url:
        return
    if not url.startswith("https://"):
        logger.warning("DISCORD_MODERATION_WEBHOOK_URL が https:// で始まらないので送りません")
        return

    payload = {
        "content": content,
        # 本文や名前に @everyone やメンションが書かれていても、誰にも通知しない
        "allowed_mentions": {"parse": []},
    }
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "User-Agent": USER_AGENT},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
            response.read()
    except Exception as e:  # noqa: BLE001 (通知の失敗で投稿を失敗させない)
        # URL (Webhook のトークンを含む) はログに出さない
        logger.warning("Discord への通知に失敗しました: %s: %s", type(e).__name__, e)


def _build(header, body, footer):
    """本文をコードブロックに入れ、全体が Discord の上限に収まるように本文を切り詰める。"""

    def render(text):
        return "\n".join([*header, _code_block(text), *footer])

    content = render(body)
    if len(content) <= MAX_CONTENT_LENGTH:
        return content
    overflow = len(content) - MAX_CONTENT_LENGTH
    return render(_escape_code_block(body)[: -(overflow + len(TRUNCATED_MARK))] + TRUNCATED_MARK)


def _code_block(text):
    # ``` の直後で改行して、本文の 1 行目が言語名として扱われないようにする
    return f"```\n{_escape_code_block(text) or '(なし)'}\n```"


def _escape_code_block(text):
    # 本文の ``` でコードブロックが閉じないように、バッククォートの間にゼロ幅スペースを挟む。
    # 切り詰めた結果に再び ``` ができないよう、_build でもこの関数を通した文字列を切る
    return (text or "").replace("```", "`​`​`")


def _inline(text):
    # 名前に書かれたリンクや装飾を効かせないように、インラインコードで囲む (` は似た文字に置き換える)
    return f"`{(text or '').replace('`', 'ˋ')}`"


def _admin_line(model_name, pk):
    path = reverse(f"admin:board_{model_name}_change", args=[pk])
    return f"管理画面: {settings.DISCORD_MODERATION_ADMIN_BASE_URL.rstrip('/')}{path}"
