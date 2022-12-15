from django.test import TestCase, Client
from django.http import HttpRequest
from board.views import Index, ThreadView, SearchView, NewQuestionsView, AboutView, TermsView, PrivacyView, ServiceWorkerView, GetAppView
from django.urls import reverse, resolve
from board.models import Thread, Post, Reply, Subject, Notice

class IndexTest(TestCase):
    # searchにリダイレクトするか
    def test_redirects_to_search(self):
        response = self.client.get(reverse('index'))
        # breakpoint()
        self.assertRedirects(response, reverse('search'))

class ThreadViewTest(TestCase):
    # テスト用のデータを作成
    def setUp(self) -> None:
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
        # breakpoint()
        # print(response.context['object_list'][0])
        self.assertEqual(response.context['object_list'][0].text, "new text2")

    # コンテキストが正しいか
    def test_context(self):
        response = self.client.get(reverse('threads', args=[1]))
        self.assertEqual(response.context['thread_title'], "test thread")
        self.assertEqual(response.context['thread_id'], 1)
        self.assertEqual(response.context['sub_title'], "test name")
        self.assertEqual(response.context['sub_teachers'], "test teachers")
        self.assertEqual(response.context['sub_codes'], "test code")


    def test_queryset(self):
        response = self.client.get(reverse('threads', args=[1]))
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
        subject1 = Subject.objects.create(code="test code", name="test name", teachers="test teachers", thread_id=thread1)
        post1 = Post.objects.create(sender_name="test sender", text="test text", emotion=0, thread=thread1)
        thread2 = Thread.objects.create(title="test thread2")
        subject2 = Subject.objects.create(code="test code2", name="test name2", teachers="test teachers2", thread_id=thread2)
        post2 = Post.objects.create(sender_name="test sender2", text="test text2", emotion=1, thread=thread2)
        thread3 = Thread.objects.create(title="test thread3")
        subject3 = Subject.objects.create(code="test code3", name="test name3", teachers="test teachers3", thread_id=thread3)
        post3 = Post.objects.create(sender_name="test sender3", text="test text3", emotion=0, thread=thread3)

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
        subject_new = Subject.objects.create(code="test_new code", name="test_new name", teachers="test_new teachers", thread_id=thread_new)
        post_new = Post.objects.create(sender_name="test_new sender", text="test_new text", thread=thread_new)
        response = self.client.get(reverse('search'))
        self.assertEqual(response.context['post_list'][0].text, "test_new text")
        self.assertEqual(response.context['post_list'][1].text, "test text3")

    # emergency rankingが正しいか
    def test_emergency_ranking(self):
        thread3 = Thread.objects.get(title="test thread3")
        post3_2 = Post.objects.create(sender_name="test sender3_2", text="test text3_2", emotion=0, thread=thread3)
        reply3_1 = Reply.objects.create(sender_name="test sender3_3", text="test text3_3", emotion=0, post_id=post3_2)
        response = self.client.get(reverse('search'))
        self.assertEqual(response.context['ranking'][0][0], 3)
        self.assertEqual(response.context['ranking'][0][1], "test thread3")
        self.assertEqual(response.context['ranking'][0][2], 3)
        self.assertEqual(response.context['ranking'][1][0], 1)
        self.assertEqual(response.context['ranking'][1][1], "test thread")
        self.assertEqual(response.context['ranking'][1][2], 1)

    # Noticeは一番新しいものが表示されるか
    def test_notice(self):
        notice = Notice.objects.create(message="test notice", is_show=True)
        response = self.client.get(reverse('search'))
        # print(response.context['notice'])
        # breakpoint()
        self.assertEqual(response.context['notice'][0]['message'], "test notice")

# class NewQuestionsView(ListView):
#     """新規投稿一覧を表示するページ"""
#     template_name = "board/NewQuestions.html"
#     model = Post

#     def get_context_data(self, *args, **kwargs):
#         context = super().get_context_data(*args, **kwargs)
#         context['post_list'] = self.model.objects.all().order_by('-created_at')[:40]
#         return context

class  NewQuestionsViewTest(TestCase):
    # テスト用のデータを作成
    def setUp(self) -> None:
        for i in range(41):
            thread = Thread.objects.create(title="test thread")
            subject = Subject.objects.create(code="test code", name="test name", teachers="test teachers", thread_id=thread)
            post = Post.objects.create(sender_name="test sender", text="test text", emotion=0, thread=thread)
        
     # NewQuestionsページのステータスコードが200か
    def test_new_questions_view(self):
        # breakpoint()
        response = self.client.get(reverse('new_questions'))
        self.assertEqual(response.status_code, 200)

    # NewQuestionsページのテンプレートが正しいか
    def test_new_questions_template(self):
        response = self.client.get(reverse('new_questions'))
        self.assertTemplateUsed(response, 'board/NewQuestions.html')

    # 新しい質問は新しい投稿が上に来るか
    def test_ordering(self):
        thread_new = Thread.objects.create(title="test_new thread")
        subject_new = Subject.objects.create(code="test_new code", name="test_new name", teachers="test_new teachers", thread_id=thread_new)
        post_new = Post.objects.create(sender_name="test_new sender", text="test_new text", thread=thread_new)
        response = self.client.get(reverse('new_questions'))
        self.assertEqual(response.context['post_list'][0].text, "test_new text")
        self.assertEqual(response.context['post_list'][1].text, "test text")

    # 40件以上の投稿は40件までしか表示されないか
    def test_post_count(self):
        response = self.client.get(reverse('new_questions'))
        self.assertEqual(len(response.context['post_list']), 40)

# class ServiceWorkerView(ListView):
#     def get(self, request, *args, **kwargs):
#         swjs = "importScripts('https://cdn.ampproject.org/sw/amp-sw.js');"
#         swjs += "AMP_SW.init();"
#         response = HttpResponse(swjs, content_type='application/javascript')
#         return response

class ServicWorkerViewTest(TestCase):
    # ServiceWorkerページのステータスコードが200か
    def test_service_worker_view(self):
        response = self.client.get('/sw.js')
        self.assertEqual(response.status_code, 200)

    # /sw.jsにアクセスするとimportScripts('https://cdn.ampproject.org/sw/amp-sw.js');AMP_SW.init();が返ってくるか
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