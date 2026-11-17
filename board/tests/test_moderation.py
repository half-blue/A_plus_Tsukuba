import json
import socket
import urllib.error
from unittest import mock

from django.db import transaction
from django.test import TestCase, override_settings
from django.urls import reverse

from board import moderation
from board.models import Post, Reply, Review, Thread

WEBHOOK_URL = "https://discord.example/api/webhooks/1/token"
ADMIN_BASE_URL = "https://www.example.com"


@override_settings(DISCORD_MODERATION_WEBHOOK_URL=WEBHOOK_URL, DISCORD_MODERATION_ADMIN_BASE_URL=ADMIN_BASE_URL)
class ModerationNotifyTest(TestCase):
    def setUp(self):
        self.thread = Thread.objects.create(title="test thread")
        patcher = mock.patch("board.moderation.urllib.request.urlopen")
        self.urlopen = patcher.start()
        self.addCleanup(patcher.stop)

    def sent_requests(self):
        return [c.args[0] for c in self.urlopen.call_args_list]

    def sent_payloads(self):
        return [json.loads(r.data) for r in self.sent_requests()]

    # API から投稿すると、Webhook に 1 回送られるか
    def test_post_via_api(self):
        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.post(reverse("api_post_subthreadss"), {
                "sender_name": "test sender", "text": "test text", "emotion": 0,
                "thread": self.thread.id, "allow_tweet": False,
            })
        self.assertEqual(response.status_code, 201)
        post = Post.objects.get()

        self.assertEqual(self.urlopen.call_count, 1)
        request = self.sent_requests()[0]
        self.assertEqual(request.full_url, WEBHOOK_URL)
        self.assertEqual(request.get_method(), "POST")
        self.assertEqual(request.get_header("Content-type"), "application/json")
        self.assertEqual(request.get_header("User-agent"), moderation.USER_AGENT)
        self.assertEqual(self.urlopen.call_args.kwargs["timeout"], moderation.TIMEOUT_SECONDS)

        payload = self.sent_payloads()[0]
        self.assertEqual(payload["allowed_mentions"], {"parse": []})
        content = payload["content"]
        self.assertIn(f"[Post: {post.post_id}]", content)
        self.assertIn("Sender: `test sender`", content)
        self.assertIn("```\ntest text\n```", content)
        self.assertIn(f"管理画面: {ADMIN_BASE_URL}/kanri/board/post/{post.post_id}/change/", content)
        self.assertNotIn("X への自動投稿", content)

    # X への自動投稿が有効な投稿には、その旨を書くか
    def test_post_allow_tweet(self):
        with self.captureOnCommitCallbacks(execute=True):
            Post.objects.create(sender_name="s", text="t", thread=self.thread, allow_tweet=True)
        self.assertIn("X への自動投稿が有効な投稿です", self.sent_payloads()[0]["content"])

    # API から返信すると送られるか
    def test_reply_via_api(self):
        post = Post.objects.create(sender_name="s", text="t", thread=self.thread)
        self.urlopen.reset_mock()
        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.post(reverse("api_post_replies"), {
                "sender_name": "reply sender", "text": "reply text", "emotion": 0, "post_id": post.post_id,
            })
        self.assertEqual(response.status_code, 201)
        reply = Reply.objects.get()
        content = self.sent_payloads()[0]["content"]
        self.assertIn(f"[Reply: {reply.reply_id}]", content)
        self.assertIn("```\nreply text\n```", content)
        self.assertIn(f"{ADMIN_BASE_URL}/kanri/board/reply/{reply.reply_id}/change/", content)

    # フォームからレビューすると送られるか
    def test_review_via_form(self):
        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.post(reverse("threads", args=[self.thread.id]), {
                "ratings_overall": 4, "ratings_easiness": 3, "ratings_content": 5, "comment": "review comment",
            })
        self.assertEqual(response.status_code, 302)
        review = Review.objects.get()
        content = self.sent_payloads()[0]["content"]
        self.assertIn(f"[Review: {review.id}]", content)
        self.assertIn("```\nreview comment\n```", content)
        self.assertIn(f"{ADMIN_BASE_URL}/kanri/board/review/{review.id}/change/", content)

    # コメントのないレビューも送るか
    def test_review_without_comment(self):
        with self.captureOnCommitCallbacks(execute=True):
            Review.objects.create(thread=self.thread, comment="")
        self.assertIn("```\n(なし)\n```", self.sent_payloads()[0]["content"])

    # 更新では送らないか
    def test_update_does_not_notify(self):
        post = Post.objects.create(sender_name="s", text="t", thread=self.thread)
        with self.captureOnCommitCallbacks(execute=True):
            post.text = "edited"
            post.save()
        self.assertEqual(self.urlopen.call_count, 0)

    # ロールバックされたものは送らないか
    def test_rollback_does_not_notify(self):
        with self.captureOnCommitCallbacks(execute=True):
            try:
                with transaction.atomic():
                    Post.objects.create(sender_name="s", text="t", thread=self.thread)
                    raise RuntimeError
            except RuntimeError:
                pass
        self.assertEqual(self.urlopen.call_count, 0)

    # 送信に失敗しても投稿は成功し、警告のログが出るか (URL はログに出さない)
    def test_failure_does_not_break_posting(self):
        for error in [
            urllib.error.HTTPError(WEBHOOK_URL, 429, "Too Many Requests", {}, None),
            urllib.error.URLError("unreachable"),
            socket.timeout("timed out"),
        ]:
            with self.subTest(error=type(error).__name__):
                self.urlopen.side_effect = error
                with self.assertLogs("board.moderation", level="WARNING") as logs:
                    with self.captureOnCommitCallbacks(execute=True):
                        response = self.client.post(reverse("api_post_subthreadss"), {
                            "sender_name": "s", "text": "t", "emotion": 0, "thread": self.thread.id,
                        })
                self.assertEqual(response.status_code, 201)
                self.assertNotIn("token", "\n".join(logs.output))

    # Webhook の URL が未設定なら送らないか
    @override_settings(DISCORD_MODERATION_WEBHOOK_URL="")
    def test_disabled_without_webhook_url(self):
        with self.captureOnCommitCallbacks(execute=True):
            Post.objects.create(sender_name="s", text="t", thread=self.thread)
        self.assertEqual(self.urlopen.call_count, 0)

    # https でない URL には送らないか
    @override_settings(DISCORD_MODERATION_WEBHOOK_URL="http://discord.example/api/webhooks/1/token")
    def test_rejects_non_https_url(self):
        with self.assertLogs("board.moderation", level="WARNING"):
            with self.captureOnCommitCallbacks(execute=True):
                Post.objects.create(sender_name="s", text="t", thread=self.thread)
        self.assertEqual(self.urlopen.call_count, 0)


@override_settings(DISCORD_MODERATION_ADMIN_BASE_URL="")
class ModerationMessageTest(TestCase):
    def setUp(self):
        self.thread = Thread.objects.create(title="test thread")

    def build(self, **kwargs):
        post = Post(sender_name="s", text="t", thread=self.thread, allow_tweet=False)
        for k, v in kwargs.items():
            setattr(post, k, v)
        return moderation.post_message(post)

    # 本文の ``` でコードブロックが閉じないか
    def test_escapes_code_fence(self):
        content = self.build(text="a```\n@everyone [x](https://example.com)\n```b")
        self.assertEqual(content.count("```"), 2)

    # 名前のバッククォートでインラインコードが閉じないか
    def test_escapes_backtick_in_sender(self):
        content = self.build(sender_name="a`[x](https://example.com)`b")
        self.assertIn("Sender: `aˋ[x](https://example.com)ˋb`", content)

    # 長い本文を切り詰めて Discord の上限に収めるか
    def test_truncates_to_discord_limit(self):
        content = self.build(text="あ" * 3000 + "```" * 100)
        self.assertEqual(len(content), moderation.MAX_CONTENT_LENGTH)
        self.assertIn(moderation.TRUNCATED_MARK + "\n```", content)
        self.assertEqual(content.count("```"), 2)
        self.assertTrue(content.rstrip().endswith("/change/"))

    # 管理画面のリンクの先頭が未設定なら、パスだけを載せるか
    def test_admin_path_without_base_url(self):
        post = Post(sender_name="s", text="t", thread=self.thread)
        self.assertIn(f"管理画面: /kanri/board/post/{post.post_id}/change/", moderation.post_message(post))
