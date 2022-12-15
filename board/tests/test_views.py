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

    def test_thread_view(self):
        response = self.client.get(reverse('threads', kwargs={'thread_id': 1}))
        self.assertEqual(response.status_code, 200)



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


