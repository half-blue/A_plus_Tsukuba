from django.db import models
from django.utils import timezone
import uuid

class Thread(models.Model):
    title    = models.CharField(verbose_name='スレタイ',blank=False, null=False, max_length=4096)
    def __str__(self):
        return self.title

class Subject(models.Model):
    internal_id = models.AutoField(verbose_name="内部id", primary_key=True)
    code = models.CharField(verbose_name="科目番号", max_length=128, default="")
    name = models.CharField(verbose_name='講義名',blank=False, null=False, max_length=4096)
    teachers =  models.TextField(verbose_name='教員名', blank=True, max_length=4096, default="")
    subtype =  models.TextField(verbose_name='種類', blank=True, max_length=1024, default="")
    schools = models.CharField(verbose_name="学群等", max_length=1024, default="", blank=True)
    colleges = models.CharField(verbose_name="学類等", max_length=1024, default="", blank=True)
    year = models.IntegerField(verbose_name="開講年度", null=True, default=None)
    thread_id = models.ForeignKey(Thread, verbose_name="スレッドid", on_delete=models.CASCADE)

    def __str__(self):
        return self.code + " " + self.name

class Post(models.Model):
    EMOTION = (
        (0, "非常事態(´•_•; )"),  # (DB値, 読みやすい値)
        (1, "考え中(-ω-;)ｳｰﾝ"),
        (2, "助かった(*´▽`人)"),
        (3, "提案(^^)/~~~"),
        (4, "ウンウン(´ー｀*)"),
        (5, "大丈夫？( *´艸｀)"),
    )

    post_id = models.UUIDField(verbose_name='投稿者id', primary_key=True, default=uuid.uuid4, editable=False)
    sender_name = models.CharField(verbose_name='投稿者名(匿名)', max_length=40, blank=False)
    text = models.TextField(verbose_name='本文', blank=False, max_length=500)
    created_at = models.DateTimeField(verbose_name='作成日時', default=timezone.now)
    thread  = models.ForeignKey(Thread, on_delete=models.CASCADE)
    emotion = models.IntegerField(choices=EMOTION, default=0)
    allow_tweet = models.BooleanField(verbose_name="ツイートする", default=True)

    def __str__(self):
        return str(self.post_id)

class Reply(models.Model):
    EMOTION = (
        (0, "非常事態(´•_•; )"),  # (DB値, 読みやすい値)
        (1, "考え中(-ω-;)ｳｰﾝ"),
        (2, "助かった(*´▽`人)"),
        (3, "提案(^^)/~~~"),
        (4, "ウンウン(´ー｀*)"),
        (5, "大丈夫？( *´艸｀)"),
    )

    post_id = models.ForeignKey(Post, on_delete=models.CASCADE, to_field="post_id")
    reply_id = models.UUIDField(verbose_name='返信id', primary_key=True, default=uuid.uuid4, editable=False)
    sender_name = models.CharField(verbose_name='投稿者名(匿名)', max_length=40, blank=False)
    text = models.TextField(verbose_name='本文', blank=False, max_length=500)
    created_at = models.DateTimeField(verbose_name='作成日時', default=timezone.now)
    emotion = models.IntegerField(choices=EMOTION, default=0)

    def __str__(self):
        return str(self.reply_id)

class Notice(models.Model):
    message = models.TextField(verbose_name='お知らせ本文', blank=False, max_length=300)
    is_show = models.BooleanField(verbose_name="公開する", default=False)
    created_at = models.DateTimeField(verbose_name='作成日時', default=timezone.now)

    def __str__(self):
        return str(self.message)
