from django.test import TestCase, Client
from django.http import HttpRequest
from board.views import Index, ThreadView, SearchView, NewQuestionsView, AboutView, TermsView, PrivacyView, ServiceWorkerView, GetAppView
from django.urls import reverse, resolve
from board.models import Thread, Post, Reply, Subject

class IndexTest(TestCase):
    def test_redirects_to_search(self):
        response = self.client.get(reverse('index'))
        # breakpoint()
        self.assertRedirects(response, reverse('search'))

class ThreadViewTest(TestCase):
    def setUp(self) -> None:
        # テスト用のデータを作成
        thread = Thread.objects.create(title="test thread")
        subject = Subject.objects.create(code="test code", name="test name", teachers="test teachers", thread_id=thread)
        post = Post.objects.create(sender_name="test sender", text="test text", thread=thread)
        reply = Reply.objects.create(sender_name="test sender", text="test text", post_id=post)

    # 存在するスレッドにアクセスした時のステータスコードが200か
    def test_status_code_200(self):
        response = self.client.get(reverse('threads', args=[1])) # /threads/1/ にアクセス
        self.assertEqual(response.status_code, 200)

    # 存在しないスレッドにアクセスした時のステータスコードが404か
    def test_status_code_404(self):
        response = self.client.get(reverse('threads', args=[2])) # /threads/2/ にアクセス
        self.assertEqual(response.status_code, 404)

    # テンプレートが正しいか
    def test_template(self):
        response = self.client.get(reverse('threads', args=[1]))
        self.assertTemplateUsed(response, 'board/Chat.html')

    # 新しい投稿が上に来るか
    def test_ordering(self):
        thread = Thread.objects.get(id=1)
        Post.objects.create(sender_name="new sender2", text="new text2", thread=thread)
        response = self.client.get(reverse('threads', args=[1]))
        self.assertEqual(response.context['object_list'][0].text, "new text2")

    def test_context(self):
        response = self.client.get(reverse('threads', args=[1]))
        self.assertEqual(response.context['thread_title'], "test thread")
        self.assertEqual(response.context['thread_id'], 1)
        self.assertEqual(response.context['sub_title'], "test name")
        self.assertEqual(response.context['sub_teachers'], "test teachers")
        self.assertEqual(response.context['sub_codes'], "test code")

    def test_404(self):
        response = self.client.get(reverse('threads', args=[2]))
        self.assertEqual(response.status_code, 404)

    def test_queryset(self):
        response = self.client.get(reverse('threads', args=[1]))
        self.assertEqual(response.context['object_list'].count(), 1)


        



class AboutViewTest(TestCase):
    def test_about_view(self):
        response = self.client.get(reverse('about'))
        self.assertEqual(response.status_code, 200)

class TermsViewTest(TestCase):
    def test_terms_view(self):
        response = self.client.get(reverse('terms'))
        self.assertEqual(response.status_code, 200)

class PrivacyViewTest(TestCase):
    def test_privacy_view(self):
        response = self.client.get(reverse('privacy'))
        self.assertEqual(response.status_code, 200)


