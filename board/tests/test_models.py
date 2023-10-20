from django.test import TestCase
from board.models import Thread, Subject, Post, Reply, Notice
import uuid

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

class PostModelTest(TestCase):
    def setUp(self) -> None:
        self.thread = Thread.objects.create(title="test thread") # 再利用するためselfにする
        self.post = Post.objects.create(sender_name="test name", text="test text", thread=self.thread)

    def test_post_id_editable(self):
        editable = self.post._meta.get_field('post_id').editable
        self.assertFalse(editable)
        # 本来はこんな感じ
        # pre_id = self.post.post_id
        # self.post.post_id = uuid.uuid4()
        # self.post.save()
        # self.assertEqual(pre_id, self.post.post_id)


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

class ReplyModelTest(TestCase):
    def setUp(self) -> None:
        self.thread = Thread.objects.create(title="test thread") # 再利用するためselfにする
        self.post = Post.objects.create(sender_name="test name", text="test text", thread=self.thread)
        self.reply = Reply.objects.create(sender_name="test name", text="test text", post_id=self.post)

    def test_post_id_on_delete(self):
        self.post.delete()
        self.assertEqual(Reply.objects.count(), 0)

    def test_reply_id_editable(self):
        editable = self.reply._meta.get_field('reply_id').editable
        self.assertFalse(editable)
        # 本来はこんな感じ
        # pre_id = self.reply.reply_id
        # self.reply.reply_id = uuid.uuid4()
        # self.reply.save()
        # self.assertEqual(pre_id, self.reply.reply_id)

    def test_sender_name_max_length(self):
        max_length = self.reply._meta.get_field('sender_name').max_length
        self.assertEquals(max_length, 40)

    def test_sender_name_blank(self):
        blank = self.reply._meta.get_field('sender_name').blank
        self.assertFalse(blank)

    def test_text_max_length(self):
        max_length = self.reply._meta.get_field('text').max_length
        self.assertEquals(max_length, 500)

    def test_text_blank(self):
        blank = self.reply._meta.get_field('text').blank
        self.assertFalse(blank)

    def test_str_method(self):
        self.assertEqual(str(self.reply), str(self.reply.reply_id))

class NoticeModelTest(TestCase):
    def setUp(self) -> None:
        self.notice = Notice.objects.create(message="test message")

    def test_message_max_length(self):
        max_length = self.notice._meta.get_field('message').max_length
        self.assertEquals(max_length, 300)

    def test_message_blank(self):
        blank = self.notice._meta.get_field('message').blank
        self.assertFalse(blank)

    def test_str_method(self):
        self.assertEqual(str(self.notice), str(self.notice.message))