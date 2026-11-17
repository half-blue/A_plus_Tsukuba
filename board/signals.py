"""投稿・返信・レビューが作られたら、モデレーション用の Discord に知らせる (board/moderation.py)。

API (投稿・返信) とフォーム (レビュー) と管理画面のどれから作っても届くように、post_save で受ける。
送るのはトランザクションがコミットされたあと (ロールバックされたものは送らない)。
フィクスチャの読み込み (raw) と、既存のものの更新では送らない。
"""

from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver

from . import moderation
from .models import Post, Reply, Review


@receiver(post_save, sender=Post, dispatch_uid="board.moderation.post")
def notify_new_post(sender, instance, created, raw, **kwargs):
    if created and not raw:
        _notify(moderation.post_message, instance)


@receiver(post_save, sender=Reply, dispatch_uid="board.moderation.reply")
def notify_new_reply(sender, instance, created, raw, **kwargs):
    if created and not raw:
        _notify(moderation.reply_message, instance)


@receiver(post_save, sender=Review, dispatch_uid="board.moderation.review")
def notify_new_review(sender, instance, created, raw, **kwargs):
    if created and not raw:
        _notify(moderation.review_message, instance)


def _notify(build_message, instance):
    if not moderation.is_enabled():
        return
    content = build_message(instance)
    transaction.on_commit(lambda: moderation.send(content))
