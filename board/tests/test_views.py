import datetime
import pytz

from django.db.models import Max
from django.test import TestCase, Client
from django.http import HttpRequest
from django.urls import reverse, resolve
from board.views import Index, ThreadView, SearchView, NewQuestionsView, AboutView, TermsView, PrivacyView, ServiceWorkerView, GetAppView
from board.models import Thread, Post, Reply, Subject, Notice

class IndexTest(TestCase):
    # searchにリダイレクトするか
    def test_redirects_to_search(self):
        response = self.client.get(reverse('index'))
        self.assertRedirects(response, reverse('search'))

class ThreadViewTest(TestCase):
    # テスト用のデータを作成
    def setUp(self) -> None:
        self.thread = Thread.objects.create(title="test thread") # 再利用するためselfにする
        subject = Subject.objects.create(code="TST0001", name="test name", teachers="test teachers", thread_id=self.thread)
        
        post_created_at = datetime.datetime(2022, 9, 20, 8, 40, 0, 0, pytz.timezone("Asia/Tokyo"))
        reply_created_at = post_created_at + datetime.timedelta(minutes=1)

        post = Post.objects.create(sender_name="test sender", text="test text", thread=self.thread, created_at=post_created_at)
        reply = Reply.objects.create(sender_name="test sender", text="test text", post_id=post, created_at=reply_created_at)

    # 存在するスレッドにアクセスした時のステータスコードが200か
    def test_thread_view_200(self):
        response = self.client.get(reverse('threads', args=[self.thread.id])) # /threads/setUPで作成したスレッドのid/ にアクセス
        self.assertEqual(response.status_code, 200)

    # 存在しないスレッドにアクセスした時のステータスコードが404か
    def test_thread_view_404(self):
        max_id = Thread.objects.all().aggregate(Max("id"))["id__max"]
        response = self.client.get(reverse('threads', args=[max_id+1])) # /threads/max(thread.id)+1/ にアクセス
        self.assertEqual(response.status_code, 404)

    # テンプレートが正しいか
    def test_template(self):
        response = self.client.get(reverse('threads', args=[self.thread.id]))
        self.assertTemplateUsed(response, 'board/Chat.html')

    # 新しい投稿が上に来るか
    def test_ordering(self):
        Post.objects.create(sender_name="new sender2", text="new text2", thread=self.thread)
        response = self.client.get(reverse('threads', args=[self.thread.id]))
        self.assertEqual(response.context['object_list'][0].text, "new text2")

    # コンテキストが正しいか
    def test_context(self):
        response = self.client.get(reverse('threads', args=[1]))
        self.assertEqual(response.context['thread_title'], "test thread")
        self.assertEqual(response.context['thread_id'], 1)
        self.assertEqual(response.context['sub_title'], "test name")
        self.assertEqual(response.context['sub_teachers'], "test teachers")
        self.assertEqual(response.context['sub_codes'], "TST0001")

    def test_queryset(self):
        response = self.client.get(reverse('threads', args=[self.thread.id]))
        self.assertEqual(response.context['object_list'].count(), 1)

class AboutViewTest(TestCase):
    # aboutページのステータスコードが200か
    def test_about_view(self):
        response = self.client.get(reverse('about'))
        self.assertEqual(response.status_code, 200)

    # aboutページのテンプレートが正しいか
    def test_about_template(self):
        response = self.client.get(reverse('about'))
        self.assertTemplateUsed(response, 'board/About.html')

class TermsViewTest(TestCase):
    # termsページのステータスコードが200か
    def test_terms_view(self):
        response = self.client.get(reverse('terms'))
        self.assertEqual(response.status_code, 200)

    # termsページのテンプレートが正しいか
    def test_terms_template(self):
        response = self.client.get(reverse('terms'))
        self.assertTemplateUsed(response, 'board/Terms.html')

class PrivacyViewTest(TestCase):
    # privacyページのステータスコードが200か
    def test_privacy_view(self):
        response = self.client.get(reverse('privacy'))
        self.assertEqual(response.status_code, 200)

    # privacyページのテンプレートが正しいか
    def test_privacy_template(self):
        response = self.client.get(reverse('privacy'))
        self.assertTemplateUsed(response, 'board/Privacy.html')

class SearchViewTest(TestCase):
    # テスト用のデータを作成
    def setUp(self) -> None:
        thread1 = Thread.objects.create(title="test thread")
        subject1 = Subject.objects.create(code="TST0001", name="test name", teachers="test teachers", thread_id=thread1)
        post1_created_at = datetime.datetime(2022, 9, 20, 8, 40, 0, 0, pytz.timezone("Asia/Tokyo"))
        post1 = Post.objects.create(sender_name="test sender", text="test text", emotion=0, thread=thread1, created_at=post1_created_at)
        thread2 = Thread.objects.create(title="test thread2")
        subject2 = Subject.objects.create(code="TST0002", name="test name2", teachers="test teachers2", thread_id=thread2)
        post2_created_at = post1_created_at + datetime.timedelta(seconds=30)
        post2 = Post.objects.create(sender_name="test sender2", text="test text2", emotion=1, thread=thread2, created_at=post2_created_at)
        thread3 = Thread.objects.create(title="test thread3")
        subject3 = Subject.objects.create(code="TST0003", name="test name3", teachers="test teachers3", thread_id=thread3)
        post3_created_at = post2_created_at + datetime.timedelta(seconds=10)
        post3 = Post.objects.create(sender_name="test sender3", text="test text3", emotion=0, thread=thread3, created_at=post3_created_at)

    # searchページのステータスコードが200か
    def test_search_view(self):
        response = self.client.get(reverse('search'))
        self.assertEqual(response.status_code, 200)

    # searchページのテンプレートが正しいか
    def test_search_template(self):
        response = self.client.get(reverse('search'))
        self.assertTemplateUsed(response, 'board/Search.html')

    # 新しい質問は新しい投稿が上に来るか
    def test_ordering(self):
        thread_new = Thread.objects.create(title="test_new thread")
        subject_new = Subject.objects.create(code="TST0004", name="test_new name", teachers="test_new teachers", thread_id=thread_new)
        post_new = Post.objects.create(sender_name="test_new sender", text="test_new text", thread=thread_new)
        response = self.client.get(reverse('search'))
        self.assertEqual(response.context['post_list'][0].text, "test_new text")
        self.assertEqual(response.context['post_list'][1].text, "test text3")

    # emergency rankingが正しいか
    def test_emergency_ranking(self):
        thread1 = Thread.objects.get(title="test thread")
        thread3 = Thread.objects.get(title="test thread3")
        post3_2 = Post.objects.create(sender_name="test sender3_2", text="test text3_2", emotion=0, thread=thread3)
        reply3_1 = Reply.objects.create(sender_name="test sender3_3", text="test text3_3", emotion=0, post_id=post3_2)
        response = self.client.get(reverse('search'))
        # (tid, title, num)
        self.assertEqual(response.context['ranking'][0][0], thread3.id)
        self.assertEqual(response.context['ranking'][0][1], "test thread3")
        self.assertEqual(response.context['ranking'][0][2], 3)
        self.assertEqual(response.context['ranking'][1][0], thread1.id)
        self.assertEqual(response.context['ranking'][1][1], "test thread")
        self.assertEqual(response.context['ranking'][1][2], 1)

    # Noticeは一番新しいものが表示されるか
    def test_notice(self):
        notice = Notice.objects.create(message="test notice", is_show=True)
        response = self.client.get(reverse('search'))
        self.assertEqual(response.context['notice'][0]['message'], "test notice")

class  NewQuestionsViewTest(TestCase):
    # テスト用のデータを作成
    def setUp(self) -> None:
        created_at = datetime.datetime(2022, 9, 20, 8, 40, 0, 0, pytz.timezone("Asia/Tokyo"))
        for i in range(41):
            thread = Thread.objects.create(title="test thread")
            subject = Subject.objects.create(code=f"TST00{i}", name="test name", teachers="test teachers", thread_id=thread)
            tdelta = datetime.timedelta(minutes=i)
            post = Post.objects.create(sender_name="test sender", text="test text", emotion=0, thread=thread, created_at=created_at+tdelta)
        
     # NewQuestionsページのステータスコードが200か
    def test_new_questions_view(self):
        response = self.client.get(reverse('new_questions'))
        self.assertEqual(response.status_code, 200)

    # NewQuestionsページのテンプレートが正しいか
    def test_new_questions_template(self):
        response = self.client.get(reverse('new_questions'))
        self.assertTemplateUsed(response, 'board/NewQuestions.html')

    # 新しい質問は新しい投稿が上に来るか
    def test_ordering(self):
        thread_new = Thread.objects.create(title="test_new thread")
        subject_new = Subject.objects.create(code="TSTNEW01", name="test_new name", teachers="test_new teachers", thread_id=thread_new)
        post_new = Post.objects.create(sender_name="test_new sender", text="test_new text", thread=thread_new)
        response = self.client.get(reverse('new_questions'))
        self.assertEqual(response.context['post_list'][0].text, "test_new text")
        self.assertEqual(response.context['post_list'][1].text, "test text")

    # 40件以上の投稿は40件までしか表示されないか
    def test_post_count(self):
        response = self.client.get(reverse('new_questions'))
        self.assertEqual(len(response.context['post_list']), 40)

class ServicWorkerViewTest(TestCase):
    # ServiceWorkerページのステータスコードが200か
    def test_service_worker_view(self):
        response = self.client.get('/sw.js')
        self.assertEqual(response.status_code, 200)

    # /sw.jsにアクセスすると適切な内容が返ってくるか
    def test_service_worker_view(self):
        response = self.client.get('/sw.js')
        swjs = "importScripts('https://cdn.ampproject.org/sw/amp-sw.js');"
        swjs += "AMP_SW.init();"
        self.assertEqual(response.content.decode('utf-8'), swjs)

class GetAppViewTest(TestCase):
    # GetAppページのステータスコードが200か
    def test_get_app_view(self):
        response = self.client.get(reverse('get_app'))
        self.assertEqual(response.status_code, 200)

    # GetAppページのテンプレートが正しいか
    def test_get_app_template(self):
        response = self.client.get(reverse('get_app'))
        self.assertTemplateUsed(response, 'board/App.html')