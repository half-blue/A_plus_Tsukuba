from django.db import models
from django.utils import timezone
import uuid

class Thread(models.Model):
    title = models.CharField(verbose_name='スレタイ', blank=False, null=False, max_length=4096)
    enable_review = models.BooleanField(verbose_name="レビュー機能を有効にする", default=True)

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
        (6, "※返信不要ヽ(｀Д´#)ﾉ"),

        # ランクに応じて追加される感情
        # Bronze 
        (10, "ｆｍ(( ˘ω ˘ *))ｆｍ"),
        (11, "ぴえん🥺"),
        # Silver
        (20, "ありがとう🙏"),
        (21, "そんな……😭"),
        # Gold
        (30, "もう無理😖"),
        (31, "異議ありっ！！"),
        (32, "🎖️GOLD🎖️"),
        # Master
        (40, "完全に理解した！"),
        (41, "どしたん話聞こか？"),
        (42, "🎓MASTER🎓"),
        # Grand Master
        (50, "IMAGINE THE FUTURE."),
        (51, "DESIGN THE FUTURE."),
        (52, "👑GRAND MASTER👑"),
    )

    post_id = models.UUIDField(verbose_name='投稿者id', primary_key=True, default=uuid.uuid4, editable=False)
    sender_name = models.CharField(verbose_name='投稿者名(匿名)', max_length=40, blank=False)
    text = models.TextField(verbose_name='本文', blank=False, max_length=500)
    created_at = models.DateTimeField(verbose_name='作成日時', default=timezone.now)
    thread  = models.ForeignKey(Thread, on_delete=models.CASCADE)
    emotion = models.IntegerField(choices=EMOTION, default=0)
    allow_tweet = models.BooleanField(verbose_name="ツイートする", default=True)
    # 投稿したときの reCAPTCHA の点数 (0.0 から 1.0。低いほど bot らしい。board/recaptcha.py)。
    # 評価できなかった投稿 (reCAPTCHA を使っていない、トークンがない・正しくない、評価の API を呼べない) と、これより前の投稿は空。
    # サーバーだけが入れる (API・フォームからは書けない)
    recaptcha_score = models.FloatField(verbose_name='点数 (reCAPTCHA)', null=True, blank=True, editable=False)

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
        (6, "※返信不要ヽ(｀Д´#)ﾉ"),

        # ランクに応じて追加される感情
        # Bronze 
        (10, "ｆｍ(( ˘ω ˘ *))ｆｍ"),
        (11, "ぴえん🥺"),
        # Silver
        (20, "ありがとう🙏"),
        (21, "そんな……😭"),
        # Gold
        (30, "もう無理😖"),
        (31, "異議ありっ！！"),
        (32, "🎖️GOLD🎖️"),
        # Master
        (40, "完全に理解した！"),
        (41, "どしたん話聞こか？"),
        (42, "🎓MASTER🎓"),
        # Grand Master
        (50, "IMAGINE THE FUTURE."),
        (51, "DESIGN THE FUTURE."),
        (52, "👑GRAND MASTER👑"),
    )

    post_id = models.ForeignKey(Post, on_delete=models.CASCADE, to_field="post_id")
    reply_id = models.UUIDField(verbose_name='返信id', primary_key=True, default=uuid.uuid4, editable=False)
    sender_name = models.CharField(verbose_name='投稿者名(匿名)', max_length=40, blank=False)
    text = models.TextField(verbose_name='本文', blank=False, max_length=500)
    created_at = models.DateTimeField(verbose_name='作成日時', default=timezone.now)
    emotion = models.IntegerField(choices=EMOTION, default=0)
    # 投稿したときの reCAPTCHA の点数 (0.0 から 1.0。低いほど bot らしい。board/recaptcha.py)。
    # 評価できなかった投稿 (reCAPTCHA を使っていない、トークンがない・正しくない、評価の API を呼べない) と、これより前の投稿は空。
    # サーバーだけが入れる (API・フォームからは書けない)
    recaptcha_score = models.FloatField(verbose_name='点数 (reCAPTCHA)', null=True, blank=True, editable=False)

    def __str__(self):
        return str(self.reply_id)

class Notice(models.Model):
    message = models.TextField(verbose_name='お知らせ本文', blank=False, max_length=300)
    is_show = models.BooleanField(verbose_name="公開する", default=False)
    created_at = models.DateTimeField(verbose_name='作成日時', default=timezone.now)

    def __str__(self):
        return str(self.message)

class Tag(models.Model):
    name = models.CharField(verbose_name='タグ名', max_length=50, blank=False)

    def __str__(self):
        return self.name

class Review(models.Model):
    RATINGS = (
        (1, '★1'),
        (2, '★★2'),
        (3, '★★★3'),
        (4, '★★★★4'),
        (5, '★★★★★5'),
    )

    thread = models.ForeignKey(Thread, verbose_name="スレッドid", on_delete=models.CASCADE)
    ratings_overall = models.IntegerField(choices=RATINGS, verbose_name='総合評価',default=3)
    ratings_easiness = models.IntegerField(choices=RATINGS, verbose_name='楽単度',default=3)
    ratings_content = models.IntegerField(choices=RATINGS, verbose_name='充実度',default=3)
    comment = models.TextField(verbose_name='コメント', blank=True, max_length=200)
    tags = models.ManyToManyField(Tag, verbose_name='タグ', blank=True)
    created_at = models.DateTimeField(verbose_name='作成日時', default=timezone.now)
    # 投稿したときの reCAPTCHA の点数 (0.0 から 1.0。低いほど bot らしい。board/recaptcha.py)。
    # 評価できなかった投稿 (reCAPTCHA を使っていない、トークンがない・正しくない、評価の API を呼べない) と、これより前の投稿は空。
    # サーバーだけが入れる (API・フォームからは書けない)
    recaptcha_score = models.FloatField(verbose_name='点数 (reCAPTCHA)', null=True, blank=True, editable=False)

    def __str__(self):
        return self.thread.title + "のレビュー"

class Textbooks(models.Model):
    thread = models.ForeignKey(Thread, verbose_name="スレッドid", on_delete=models.CASCADE)
    textbooks_json_object = models.TextField(verbose_name="教科書情報JSON", blank=True, default="{}")

    """
    textbooks_json_objectは以下のようなJSONを想定している
    文字列は本来PythonでUnicodeエスケープされている。
    例えば、"\\u6559\\u79d1\\u66f8"は"教科書"である。
    ここでは簡便のため、エスケープせず例を示す。

    4676: データベース概論A
    {
    "rows": [
        {
            "row": [
                {
                    "text": "以下を教科書とする.",
                    "is_link": false
                }
            ]
        },
        {
            "row": [
                {
                    "text": "1. 北川博之 「",
                    "is_link": false
                },
                {
                    "text": "データベースシステム 改訂2版",
                    "is_link": true
                },
                {
                    "text": "」(オーム社)",
                    "is_link": false
                }
            ]
        }
    ]
    """

    class Meta:
        verbose_name_plural = "Textbooks"

    def __str__(self):
        return self.thread.title + "の教科書情報JSON"
