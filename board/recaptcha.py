"""質問・返信・レビューの投稿を、reCAPTCHA (Google Cloud Fraud Defense) の score 型の鍵で bot から守る。

- ブラウザ (board/static/board/recaptcha.js) が投稿の直前にトークンを取り、投稿と一緒に送る (フィールド名は TOKEN_FIELD)。
  サーバーはトークンで評価 (assessment) を作り、トークンが正しいか・アクションが合っているか・点数がしきい値以上かを確かめる。
- 設定 RECAPTCHA_SITE_KEY と RECAPTCHA_PROJECT_ID (環境変数) のどちらかが未設定なら何もしない (ローカルの開発環境やテスト)。
- 設定 RECAPTCHA_MODE で動きを切り替える。
  - log: 評価して記録するだけで、投稿は断らない。しきい値を決めるまでの期間に使う。
    本番の設定ではログが WARNING 以上しか出ないので、評価の結果はすべて WARNING で残す
  - enforce: トークンがない・正しくない・アクションが違う・点数が RECAPTCHA_SCORE_THRESHOLD 未満の投稿を断る
- トークンがない投稿では評価を作らない (評価の数だけ課金されるため。bot がトークンなしで送ってきても費用はかからない)。
- トークンが正しければ、点数を投稿と一緒に保存する (Post・Reply・Review の recaptcha_score。それ以外は空)。
- 評価の API を呼べなかったとき (タイムアウトや権限の誤りなど) は投稿を通し、警告のログだけを残す。
  reCAPTCHA の障害で投稿できなくなるのを避けるため。
- 認証は Cloud Run の実行 SA を使う (メタデータサーバーからアクセストークンを取る)。
  SA に reCAPTCHA Enterprise Agent (roles/recaptchaenterprise.agent) のロールが要る。
"""

import json
import logging
import threading
import time
import urllib.parse
import urllib.request
from collections.abc import Mapping
from dataclasses import dataclass

from django.conf import settings

logger = logging.getLogger(__name__)

# ブラウザが execute() に渡すアクション名 (board/static/board/recaptcha.js と揃える)。英字と _ だけが使える
ACTION_POST_QUESTION = "post_question"
ACTION_POST_REPLY = "post_reply"
ACTION_POST_REVIEW = "post_review"

# 投稿 (API の JSON とレビューのフォーム) の中でトークンを入れるフィールドの名前
TOKEN_FIELD = "recaptcha_token"

# 断ったときに利用者に見せる文
REJECTED_MESSAGE = "投稿できませんでした。ページを再読み込みしてから、もう一度お試しください。"

MODE_LOG = "log"
MODE_ENFORCE = "enforce"

# API とメタデータサーバーのタイムアウト (秒)。投稿のレスポンスはこの分だけ遅れうる
TIMEOUT_SECONDS = 3

ASSESSMENTS_URL = "https://recaptchaenterprise.googleapis.com/v1/projects/{project}/assessments"
METADATA_TOKEN_URL = "http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/token"

# アプリ (iOS/Android) はサイトを WebView で表示していて、User-Agent にこの文字列を含む (board/templates/load_javascript.html)。
# WebView では reCAPTCHA の点数がブラウザと違う出方をするおそれがあるので、ログで分けて見られるようにする
APP_USER_AGENT_MARK = "A+Tsukuba-flutter-App"

# アクセストークンの期限の何秒前に取り直すか
ACCESS_TOKEN_REFRESH_MARGIN_SECONDS = 60

_access_token_lock = threading.Lock()
_access_token = None
_access_token_expires_at = 0.0


class AssessmentError(Exception):
    """評価を作れなかった (API やメタデータサーバーを呼べなかった、応答が読めなかった)。"""


@dataclass(frozen=True)
class Verdict:
    """verify の結果。"""

    # 投稿を通してよいか
    allowed: bool
    # 投稿と一緒に保存する点数 (モデルの recaptcha_score)。トークンが正しいときだけ入る。
    # reCAPTCHA を使わないとき、トークンがない・正しくないとき、評価を作れなかったときは None
    score: float | None = None


def is_enabled():
    return bool(settings.RECAPTCHA_SITE_KEY and settings.RECAPTCHA_PROJECT_ID)


def site_key():
    """ページに埋め込む鍵。使わないときは空文字列。"""
    return settings.RECAPTCHA_SITE_KEY if is_enabled() else ""


def token_from(data):
    """投稿のデータ (request.data や request.POST) からトークンを取り出す。なければ空文字列。"""
    if not isinstance(data, Mapping):
        return ""
    token = data.get(TOKEN_FIELD)
    return token if isinstance(token, str) else ""


def verify(request, token, action):
    """投稿を通してよいかと、保存する点数を返す (Verdict)。
    reCAPTCHA を使わないとき、log のとき、評価を作れなかったときは通す。"""
    if not is_enabled():
        return Verdict(allowed=True)

    mode = _mode()
    context = {
        "action": action,
        "mode": mode,
        "app": APP_USER_AGENT_MARK in request.META.get("HTTP_USER_AGENT", ""),
    }

    if not token:
        return Verdict(allowed=_decide(mode, "missing_token", context))

    try:
        assessment = create_assessment(token, action, request.META.get("HTTP_USER_AGENT", ""))
    except AssessmentError as e:
        logger.warning("reCAPTCHA: 評価を作れなかったので投稿を通します: %s %s", e, _format(context))
        return Verdict(allowed=True)

    token_properties = assessment.get("tokenProperties") or {}
    risk_analysis = assessment.get("riskAnalysis") or {}
    score = risk_analysis.get("score")
    context.update(
        score=score,
        reasons=",".join(risk_analysis.get("reasons") or []) or "-",
        hostname=token_properties.get("hostname"),
    )

    if token_properties.get("valid") is not True:
        context["invalid_reason"] = token_properties.get("invalidReason")
        return Verdict(allowed=_decide(mode, "invalid_token", context))

    # トークンが正しければ、点数を投稿と一緒に保存する (アクションが違うとき・しきい値未満のときも、log で通すなら残す)
    saved_score = float(score) if isinstance(score, (int, float)) else None
    if token_properties.get("action") != action:
        context["token_action"] = token_properties.get("action")
        return Verdict(allowed=_decide(mode, "action_mismatch", context), score=saved_score)
    if saved_score is None or saved_score < settings.RECAPTCHA_SCORE_THRESHOLD:
        context["threshold"] = settings.RECAPTCHA_SCORE_THRESHOLD
        return Verdict(allowed=_decide(mode, "low_score", context), score=saved_score)
    return Verdict(allowed=_decide(mode, "ok", context), score=saved_score)


def create_assessment(token, action, user_agent):
    """評価を作り、応答の JSON (dict) を返す。

    userIpAddress は送らない。LB (Cloud Load Balancing) と Cloud Run を通ると X-Forwarded-For に複数の IP が並び、
    利用者の IP を取り違えると (LB の IP を送るなど) かえって判定を損ねるおそれがあるため。
    """
    url = ASSESSMENTS_URL.format(project=urllib.parse.quote(settings.RECAPTCHA_PROJECT_ID, safe=""))
    body = {
        "event": {
            "token": token,
            "siteKey": settings.RECAPTCHA_SITE_KEY,
            "expectedAction": action,
            "userAgent": user_agent,
        }
    }
    request = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {_get_access_token()}",
            "Content-Type": "application/json; charset=utf-8",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
            assessment = json.load(response)
    except Exception as e:  # noqa: BLE001 (HTTP のエラー、タイムアウト、JSON でない応答をまとめて扱う)
        raise AssessmentError(f"評価の API: {type(e).__name__}: {e}") from e
    if not isinstance(assessment, dict):
        raise AssessmentError("評価の API: 応答が JSON のオブジェクトではありません")
    return assessment


def _get_access_token():
    """Cloud Run の実行 SA のアクセストークン。期限の少し前まで使い回す。"""
    global _access_token, _access_token_expires_at
    with _access_token_lock:
        now = time.monotonic()
        if _access_token and now < _access_token_expires_at - ACCESS_TOKEN_REFRESH_MARGIN_SECONDS:
            return _access_token
        request = urllib.request.Request(METADATA_TOKEN_URL, headers={"Metadata-Flavor": "Google"})
        try:
            with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
                data = json.load(response)
            token = data["access_token"]
            expires_in = float(data["expires_in"])
        except Exception as e:  # noqa: BLE001 (メタデータサーバーがない環境、応答の形の違いなどをまとめて扱う)
            raise AssessmentError(f"アクセストークン: {type(e).__name__}: {e}") from e
        _access_token = token
        _access_token_expires_at = now + expires_in
        return token


def _mode():
    mode = settings.RECAPTCHA_MODE
    if mode in (MODE_LOG, MODE_ENFORCE):
        return mode
    logger.warning("reCAPTCHA: RECAPTCHA_MODE=%r は log か enforce にしてください。log として扱います", mode)
    return MODE_LOG


def _decide(mode, outcome, context):
    allowed = outcome == "ok" or mode == MODE_LOG
    context = {"outcome": outcome, "allowed": allowed, **context}
    # log のときはしきい値を決めるために全件を残す。enforce のときは断ったものだけを残す
    if mode == MODE_LOG or not allowed:
        logger.warning("reCAPTCHA: %s", _format(context))
    else:
        logger.info("reCAPTCHA: %s", _format(context))
    return allowed


def _format(context):
    return " ".join(f"{k}={v}" for k, v in context.items())
