import json
import urllib.error
from unittest import mock

from django.test import TestCase, override_settings
from django.urls import reverse

from board import recaptcha
from board.models import Post, Reply, Review, Subject, Thread

SITE_KEY = "test-site-key"
PROJECT_ID = "test-project"
ACCESS_TOKEN = "test-access-token"

ENABLED = {
    "RECAPTCHA_SITE_KEY": SITE_KEY,
    "RECAPTCHA_PROJECT_ID": PROJECT_ID,
    "RECAPTCHA_SCORE_THRESHOLD": 0.5,
    # Discord への通知は送らない (送り先が設定されていれば urlopen が呼ばれ、このテストの数え方が狂う)
    "DISCORD_MODERATION_WEBHOOK_URL": "",
}


def assessment(valid=True, action=recaptcha.ACTION_POST_QUESTION, score=0.9, invalid_reason=None):
    token_properties = {"valid": valid, "action": action, "hostname": "www.example.com"}
    if invalid_reason:
        token_properties["invalidReason"] = invalid_reason
    return {"tokenProperties": token_properties, "riskAnalysis": {"score": score, "reasons": []}}


class FakeResponse:
    def __init__(self, body):
        self.body = json.dumps(body).encode("utf-8")

    def read(self, *args):
        return self.body

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


class RecaptchaTestCase(TestCase):
    """urlopen を差し替えて、メタデータサーバーと評価の API の応答を決める。"""

    def setUp(self):
        self.thread = Thread.objects.create(title="test thread", enable_review=True)
        Subject.objects.create(code="GA00000", name="test subject", thread_id=self.thread, year=2026)
        self.assessment_response = assessment()
        self.assessment_error = None
        patcher = mock.patch("board.recaptcha.urllib.request.urlopen", side_effect=self.fake_urlopen)
        self.urlopen = patcher.start()
        self.addCleanup(patcher.stop)
        # アクセストークンの使い回しをテストごとに消す
        recaptcha._access_token = None
        recaptcha._access_token_expires_at = 0.0

    def fake_urlopen(self, request, timeout=None):
        if request.full_url == recaptcha.METADATA_TOKEN_URL:
            return FakeResponse({"access_token": ACCESS_TOKEN, "expires_in": 3599, "token_type": "Bearer"})
        if self.assessment_error:
            raise self.assessment_error
        return FakeResponse(self.assessment_response)

    def assessment_requests(self):
        return [
            c.args[0] for c in self.urlopen.call_args_list
            if c.args[0].full_url != recaptcha.METADATA_TOKEN_URL
        ]

    def post_question(self, token="test-token", user_agent="test-agent"):
        data = {"sender_name": "s", "text": "t", "emotion": 0, "thread": self.thread.id, "allow_tweet": False}
        if token is not None:
            data[recaptcha.TOKEN_FIELD] = token
        return self.client.post(
            reverse("api_post_subthreadss"), data, content_type="application/json", HTTP_USER_AGENT=user_agent,
        )

    def post_reply(self, token="test-token"):
        post = Post.objects.create(sender_name="s", text="t", thread=self.thread)
        data = {"sender_name": "s", "text": "t", "emotion": 0, "post_id": post.post_id, recaptcha.TOKEN_FIELD: token}
        return self.client.post(reverse("api_post_replies"), data, content_type="application/json")

    def post_review(self, token="test-token"):
        data = {"ratings_overall": 3, "ratings_easiness": 3, "ratings_content": 3, "comment": "c"}
        if token is not None:
            data[recaptcha.TOKEN_FIELD] = token
        return self.client.post(reverse("threads", kwargs={"thread_id": self.thread.id}), data)


@override_settings(RECAPTCHA_SITE_KEY="", RECAPTCHA_PROJECT_ID="", DISCORD_MODERATION_WEBHOOK_URL="")
class DisabledTest(RecaptchaTestCase):
    # 鍵が未設定なら、トークンなしで投稿でき、評価も作らないか
    def test_post_without_token(self):
        response = self.post_question(token=None)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(self.urlopen.call_count, 0)

    # 鍵が未設定なら、点数は空のまま保存するか。クライアントが点数を送っても保存しないか
    def test_score_is_null_and_not_writable(self):
        data = {"sender_name": "s", "text": "t", "emotion": 0, "thread": self.thread.id, "recaptcha_score": 1.0}
        response = self.client.post(reverse("api_post_subthreadss"), data, content_type="application/json")
        self.assertEqual(response.status_code, 201)
        self.assertIsNone(Post.objects.get().recaptcha_score)
        self.assertNotIn("recaptcha_score", response.json())

        post = Post.objects.get()
        data = {"sender_name": "s", "text": "t", "emotion": 0, "post_id": post.post_id, "recaptcha_score": 1.0}
        self.client.post(reverse("api_post_replies"), data, content_type="application/json")
        self.assertIsNone(Reply.objects.get().recaptcha_score)

        data = {"ratings_overall": 3, "ratings_easiness": 3, "ratings_content": 3, "recaptcha_score": 1.0}
        self.client.post(reverse("threads", kwargs={"thread_id": self.thread.id}), data)
        self.assertIsNone(Review.objects.get().recaptcha_score)

    # 鍵が未設定なら、スレッドのページに reCAPTCHA を載せないか
    def test_thread_page_has_no_script(self):
        response = self.client.get(reverse("threads", kwargs={"thread_id": self.thread.id}))
        self.assertNotContains(response, "recaptcha/enterprise.js")
        self.assertNotContains(response, 'name="recaptcha_token"')
        self.assertNotContains(response, "reCAPTCHA で保護されており")


@override_settings(**ENABLED, RECAPTCHA_MODE="enforce")
class EnforceTest(RecaptchaTestCase):
    # 正しいトークンで点数が高ければ投稿でき、評価の API に正しい内容を送るか
    def test_valid_token(self):
        response = self.post_question(user_agent="Mozilla/5.0 test")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Post.objects.get().recaptcha_score, 0.9)

        [request] = self.assessment_requests()
        self.assertEqual(
            request.full_url, f"https://recaptchaenterprise.googleapis.com/v1/projects/{PROJECT_ID}/assessments"
        )
        self.assertEqual(request.get_method(), "POST")
        self.assertEqual(request.get_header("Authorization"), f"Bearer {ACCESS_TOKEN}")
        self.assertEqual(json.loads(request.data), {
            "event": {
                "token": "test-token",
                "siteKey": SITE_KEY,
                "expectedAction": recaptcha.ACTION_POST_QUESTION,
                "userAgent": "Mozilla/5.0 test",
            }
        })

    # トークンがなければ、評価を作らずに断るか
    def test_missing_token(self):
        with self.assertLogs("board.recaptcha", "WARNING"):
            response = self.post_question(token=None)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()["detail"], recaptcha.REJECTED_MESSAGE)
        self.assertEqual(Post.objects.count(), 0)
        self.assertEqual(self.urlopen.call_count, 0)

    # トークンが文字列でなければ、ないものとして扱うか
    def test_non_string_token(self):
        with self.assertLogs("board.recaptcha", "WARNING"):
            response = self.post_question(token=12345)
        self.assertEqual(response.status_code, 403)
        self.assertEqual(self.urlopen.call_count, 0)

    # 入力が正しくない投稿には評価を作らないか
    def test_invalid_input_is_not_assessed(self):
        response = self.client.post(
            reverse("api_post_subthreadss"),
            {"sender_name": "s", "text": "t", "emotion": 0, recaptcha.TOKEN_FIELD: "test-token"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(self.urlopen.call_count, 0)

    # 点数がしきい値未満なら断るか
    def test_low_score(self):
        self.assessment_response = assessment(score=0.3)
        with self.assertLogs("board.recaptcha", "WARNING") as logs:
            response = self.post_question()
        self.assertEqual(response.status_code, 403)
        self.assertEqual(Post.objects.count(), 0)
        self.assertIn("outcome=low_score", logs.output[0])

    # 点数がしきい値ちょうどなら通すか
    def test_score_equal_to_threshold(self):
        self.assessment_response = assessment(score=0.5)
        self.assertEqual(self.post_question().status_code, 201)

    # トークンが正しくなければ断るか
    def test_invalid_token(self):
        self.assessment_response = assessment(valid=False, invalid_reason="MALFORMED")
        with self.assertLogs("board.recaptcha", "WARNING") as logs:
            response = self.post_question()
        self.assertEqual(response.status_code, 403)
        self.assertIn("invalid_reason=MALFORMED", logs.output[0])

    # 別のアクションで取ったトークンなら断るか
    def test_action_mismatch(self):
        self.assessment_response = assessment(action=recaptcha.ACTION_POST_REPLY)
        with self.assertLogs("board.recaptcha", "WARNING"):
            response = self.post_question()
        self.assertEqual(response.status_code, 403)

    # 評価の API を呼べなければ、投稿を通すか
    def test_api_error_fails_open(self):
        self.assessment_error = urllib.error.URLError("timed out")
        with self.assertLogs("board.recaptcha", "WARNING") as logs:
            response = self.post_question()
        self.assertEqual(response.status_code, 201)
        self.assertIn("評価を作れなかった", logs.output[0])
        self.assertIsNone(Post.objects.get().recaptcha_score)

    # アクセストークンを使い回すか
    def test_access_token_is_reused(self):
        self.post_question()
        self.post_question()
        metadata_calls = [
            c for c in self.urlopen.call_args_list if c.args[0].full_url == recaptcha.METADATA_TOKEN_URL
        ]
        self.assertEqual(len(metadata_calls), 1)
        self.assertEqual(metadata_calls[0].args[0].get_header("Metadata-flavor"), "Google")

    # 返信は post_reply のアクションで確かめるか
    def test_reply(self):
        self.assessment_response = assessment(action=recaptcha.ACTION_POST_REPLY)
        response = self.post_reply()
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Reply.objects.get().recaptcha_score, 0.9)
        [request] = self.assessment_requests()
        self.assertEqual(json.loads(request.data)["event"]["expectedAction"], recaptcha.ACTION_POST_REPLY)

    # 返信も点数が低ければ断るか
    def test_reply_low_score(self):
        self.assessment_response = assessment(action=recaptcha.ACTION_POST_REPLY, score=0.1)
        with self.assertLogs("board.recaptcha", "WARNING"):
            response = self.post_reply()
        self.assertEqual(response.status_code, 403)
        self.assertEqual(Reply.objects.count(), 0)

    # レビューは post_review のアクションで確かめて保存するか
    def test_review(self):
        self.assessment_response = assessment(action=recaptcha.ACTION_POST_REVIEW)
        response = self.post_review()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Review.objects.get().recaptcha_score, 0.9)
        [request] = self.assessment_requests()
        self.assertEqual(json.loads(request.data)["event"]["expectedAction"], recaptcha.ACTION_POST_REVIEW)

    # レビューも点数が低ければ保存せず、フォームに理由を出すか
    def test_review_low_score(self):
        self.assessment_response = assessment(action=recaptcha.ACTION_POST_REVIEW, score=0.1)
        with self.assertLogs("board.recaptcha", "WARNING"):
            response = self.post_review()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Review.objects.count(), 0)
        self.assertContains(response, recaptcha.REJECTED_MESSAGE)

    # レビューにトークンがなければ、評価を作らずに断るか
    def test_review_missing_token(self):
        with self.assertLogs("board.recaptcha", "WARNING"):
            response = self.post_review(token=None)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Review.objects.count(), 0)
        self.assertEqual(self.urlopen.call_count, 0)

    # スレッドのページに reCAPTCHA の読み込み・鍵・レビューの隠しフィールドを載せるか
    def test_thread_page_has_script(self):
        response = self.client.get(reverse("threads", kwargs={"thread_id": self.thread.id}))
        self.assertContains(response, f"https://www.google.com/recaptcha/enterprise.js?render={SITE_KEY}")
        self.assertContains(response, f'<script id="recaptcha-site-key" type="application/json">"{SITE_KEY}"</script>')
        self.assertContains(response, 'name="recaptcha_token"')
        self.assertContains(response, "board/recaptcha.js")
        # 質問・返信のフォームとレビューのフォームの 2 か所に、reCAPTCHA を使っていることを書く
        self.assertContains(response, "このサイトは reCAPTCHA で保護されており", count=2)
        # (ページには既存の <input ...></input> があり HTML として読めないので、html=True では比べない)
        # リンクは新しいタブで開く (フォームに書きかけの本文が消えないように)
        new_tab = 'target="_blank" rel="noopener"'
        self.assertContains(
            response, f'<a href="https://policies.google.com/privacy" {new_tab}>プライバシーポリシー</a>', count=2,
        )
        self.assertContains(response, f'<a href="https://policies.google.com/terms" {new_tab}>利用規約</a>', count=2)
        self.assertContains(response, f'<a href="/terms/" {new_tab}>利用規約</a>', count=2)
        # 質問・返信のフォームとレビューのフォームの 2 か所に、投稿で利用規約に同意したとみなすことを書く
        self.assertContains(response, "投稿することにより、", count=2)
        self.assertContains(response, "に同意したものとみなされます。", count=2)


@override_settings(**ENABLED, RECAPTCHA_MODE="log")
class LogModeTest(RecaptchaTestCase):
    # log では、トークンがなくても投稿でき、記録だけするか
    def test_missing_token(self):
        with self.assertLogs("board.recaptcha", "WARNING") as logs:
            response = self.post_question(token=None)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(self.urlopen.call_count, 0)
        self.assertIn("outcome=missing_token", logs.output[0])
        self.assertIn("allowed=True", logs.output[0])
        self.assertIsNone(Post.objects.get().recaptcha_score)

    # log では、点数が低くても投稿でき、点数を記録するか
    def test_low_score(self):
        self.assessment_response = assessment(score=0.1)
        with self.assertLogs("board.recaptcha", "WARNING") as logs:
            response = self.post_question()
        self.assertEqual(response.status_code, 201)
        self.assertIn("outcome=low_score", logs.output[0])
        self.assertIn("score=0.1", logs.output[0])
        self.assertEqual(Post.objects.get().recaptcha_score, 0.1)

    # log では、トークンが正しくなければ点数は空で保存するか
    def test_invalid_token_score_is_null(self):
        self.assessment_response = assessment(valid=False, score=0.0, invalid_reason="EXPIRED")
        with self.assertLogs("board.recaptcha", "WARNING"):
            response = self.post_question()
        self.assertEqual(response.status_code, 201)
        self.assertIsNone(Post.objects.get().recaptcha_score)

    # log では、アクションが違っても点数を保存するか (トークンは正しいので)
    def test_action_mismatch_keeps_score(self):
        self.assessment_response = assessment(action=recaptcha.ACTION_POST_REVIEW, score=0.7)
        with self.assertLogs("board.recaptcha", "WARNING"):
            response = self.post_question()
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Post.objects.get().recaptcha_score, 0.7)

    # log では、通る投稿も記録するか (しきい値を決めるため)。アプリ (WebView) からの投稿かも残すか
    def test_ok_is_logged_with_app_flag(self):
        with self.assertLogs("board.recaptcha", "WARNING") as logs:
            self.post_question(user_agent="Mozilla/5.0 A+Tsukuba-flutter-App")
        self.assertIn("outcome=ok", logs.output[0])
        self.assertIn("app=True", logs.output[0])

    # ログにトークンを出さないか
    def test_token_is_not_logged(self):
        with self.assertLogs("board.recaptcha", "WARNING") as logs:
            self.post_question(token="secret-token-value")
        self.assertNotIn("secret-token-value", "\n".join(logs.output))


@override_settings(**ENABLED, RECAPTCHA_MODE="typo")
class UnknownModeTest(RecaptchaTestCase):
    # RECAPTCHA_MODE が log・enforce 以外なら log として扱う (断らない) か
    def test_unknown_mode_is_log(self):
        with self.assertLogs("board.recaptcha", "WARNING"):
            response = self.post_question(token=None)
        self.assertEqual(response.status_code, 201)


class AdminTest(TestCase):
    """管理画面に reCAPTCHA の点数 (recaptcha_score) を出し、書き換えさせないか。"""

    def setUp(self):
        from django.contrib.auth import get_user_model

        admin_user = get_user_model().objects.create_superuser("admin", "admin@example.com", "password")
        self.client.force_login(admin_user)
        self.thread = Thread.objects.create(title="test thread")
        self.post = Post.objects.create(sender_name="s", text="t", thread=self.thread, recaptcha_score=0.3)
        self.reply = Reply.objects.create(sender_name="s", text="t", post_id=self.post, recaptcha_score=0.7)
        self.review = Review.objects.create(thread=self.thread, recaptcha_score=0.9)

    # 一覧に点数の列が出るか
    def test_changelist_shows_score(self):
        for model_name, score in (("post", "0.3"), ("reply", "0.7"), ("review", "0.9")):
            with self.subTest(model_name=model_name):
                response = self.client.get(reverse(f"admin:board_{model_name}_changelist"))
                self.assertContains(response, "column-recaptcha_score")
                self.assertContains(response, "点数 (reCAPTCHA)")
                self.assertContains(response, f'<td class="field-recaptcha_score">{score}</td>', html=True)

    # 編集画面に点数が出て、入力欄にはならないか
    def test_change_form_shows_score_read_only(self):
        for model_name, pk, score in (
            ("post", self.post.pk, "0.3"), ("reply", self.reply.pk, "0.7"), ("review", self.review.pk, "0.9"),
        ):
            with self.subTest(model_name=model_name):
                response = self.client.get(reverse(f"admin:board_{model_name}_change", args=[pk]))
                # 項目名は先頭を大文字にされない日本語で始める (「ReCAPTCHA」と表示させない)
                self.assertContains(response, "<label>点数 (reCAPTCHA):</label>", html=True)
                self.assertContains(response, f'<div class="readonly">{score}</div>', html=True)
                self.assertNotContains(response, 'name="recaptcha_score"')

    # 編集画面から点数を送っても書き換わらないか
    def test_change_form_does_not_update_score(self):
        url = reverse("admin:board_post_change", args=[self.post.pk])
        response = self.client.post(url, {
            "sender_name": "s", "text": "t", "created_at_0": "2026-11-16", "created_at_1": "00:00:00",
            "thread": self.thread.pk, "emotion": 0, "allow_tweet": "on", "recaptcha_score": "1.0",
        })
        self.assertEqual(response.status_code, 302)
        self.post.refresh_from_db()
        self.assertEqual(self.post.recaptcha_score, 0.3)
