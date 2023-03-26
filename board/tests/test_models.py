from django.test import TestCase
from board.models import Thread, Subject, Post, Reply, Notice

"""
現在のmariaDBの設定はStrict Modeではないため、厳密なmodelのテストは行えない。
例えば、Threadモデルはmax_lengthに設定されてある値以上も保存できるし、
blank=Falseにしても、空文字を保存できる。
そのため、厳密なテストは行わず、モデルの_meta情報の定義よりテストを行う。
本当は、実際にmax_lengthを超えた場合にエラーになるかどうかやblankがバリデーションに
ひっかかることをテストしたい。
(_metaでテストを行うのは本質的なテストではないため。)

※mariaDBをstrict modeにする場合は@nitocaにまた言ってください。
"""


class ThreadModelTest(TestCase):
    # テスト用のデータを作成
    def setUp(self) -> None:
        self.thread = Thread.objects.create(title="test thread") # 再利用するためselfにする

    def test_title_max_length(self):
        max_length = self.thread._meta.get_field('title').max_length
        self.assertEquals(max_length, 150)

    def test_title_blank_null(self):
        blank = self.thread._meta.get_field('title').blank
        null = self.thread._meta.get_field('title').null
        self.assertFalse(blank)
        self.assertFalse(null)
        
    def test_str_method(self):
        self.assertEqual(str(self.thread), self.thread.title)

"""
class Subject(models.Model):
    internal_id = models.AutoField(verbose_name="内部id", primary_key=True)
    code = models.CharField(verbose_name="科目番号", max_length=10, default="")
    name = models.CharField(verbose_name='講義名',blank=False, null=False, max_length=150)
    teachers =  models.TextField(verbose_name='教員名', blank=True, max_length=100, default="")
    subtype =  models.TextField(verbose_name='種類', blank=True, max_length=32, default="")
    schools = models.CharField(verbose_name="学群等", max_length=40, default="", blank=True)
    colleges = models.CharField(verbose_name="学類等", max_length=40, default="", blank=True)
    thread_id = models.ForeignKey(Thread, verbose_name="スレッドid", on_delete=models.CASCADE)

    def __str__(self):
        return self.code + " " + self.name
"""
class SubjectModelTest(TestCase):
    def setUp(self) -> None:
        self.thread = Thread.objects.create(title="test thread") # 再利用するためselfにする
        self.subject = Subject.objects.create(code="TST0001", name="test name", thread_id=self.thread)

    def test_code_max_length(self):
        max_length = self.subject._meta.get_field('code').max_length
        self.assertEquals(max_length, 10)

    def test_name_max_length(self):
        max_length = self.subject._meta.get_field('name').max_length
        self.assertEquals(max_length, 150)

    def test_name_blank_null(self):
        blank = self.subject._meta.get_field('name').blank
        null = self.subject._meta.get_field('name').null
        self.assertFalse(blank)
        self.assertFalse(null)

    def test_teachers_max_length(self):
        max_length = self.subject._meta.get_field('teachers').max_length
        self.assertEquals(max_length, 100)

    def test_teachers_blank(self):
        blank = self.subject._meta.get_field('teachers').blank
        self.assertTrue(blank)

    def test_subtype_max_length(self):
        max_length = self.subject._meta.get_field('subtype').max_length
        self.assertEquals(max_length, 32)

    def test_subtype_blank(self):
        blank = self.subject._meta.get_field('subtype').blank
        self.assertTrue(blank)

    def test_schools_max_length(self):
        max_length = self.subject._meta.get_field('schools').max_length
        self.assertEquals(max_length, 40)

    def test_schools_blank(self):
        blank = self.subject._meta.get_field('schools').blank
        self.assertTrue(blank)

    def test_colleges_max_length(self):
        max_length = self.subject._meta.get_field('colleges').max_length
        self.assertEquals(max_length, 40)

    def test_colleges_blank(self):
        blank = self.subject._meta.get_field('colleges').blank
        self.assertTrue(blank)

    def test_thread_id_on_delete(self):
        self.thread.delete()
        self.assertEqual(Subject.objects.count(), 0)

    def test_str_method(self):
        self.assertEqual(str(self.subject), self.subject.code + " " + self.subject.name)

"""
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

    def __str__(self):
        return str(self.post_id)
"""

class PostModelTest(TestCase):
    def setUp(self) -> None:
        self.thread = Thread.objects.create(title="test thread") # 再利用するためselfにする
        self.post = Post.objects.create(sender_name="test name", text="test text", thread=self.thread)

    def test_sender_name_max_length(self):
        max_length = self.post._meta.get_field('sender_name').max_length
        self.assertEquals(max_length, 40)

    def test_sender_name_blank(self):
        blank = self.post._meta.get_field('sender_name').blank
        self.assertFalse(blank)

    def test_text_max_length(self):
        max_length = self.post._meta.get_field('text').max_length
        self.assertEquals(max_length, 500)

    def test_text_blank(self):
        blank = self.post._meta.get_field('text').blank
        self.assertFalse(blank)

    def test_thread_on_delete(self):
        self.thread.delete()
        self.assertEqual(Post.objects.count(), 0)

    def test_str_method(self):
        self.assertEqual(str(self.post), str(self.post.post_id))
