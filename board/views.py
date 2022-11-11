from django.shortcuts import render
from django.http import HttpResponse, Http404
from .models import Notice, Post, Reply, Subject, Thread
from django.shortcuts import redirect
from django.views.generic import TemplateView, ListView
from django.db.models import Count

class Index(ListView):
    def get(self, request, *args, **kwargs):
        return redirect("search/")


class ThreadView(ListView):
    template_name = "board/Chat.html"
    model = Post
    #context_object_name = 'post_data'
    ordering = ['-created_at']

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        thread_id = self.kwargs['thread_id']
        try:
            thread = Thread.objects.get(id = thread_id)
        except Thread.DoesNotExist:
            raise Http404()

        context['thread_title'] = thread.title
        context['thread_id'] = thread_id

        # 科目情報
        sub_col = Subject.objects.filter(thread_id = thread_id).values()[0]
        context['sub_title'] = sub_col["name"]
        context['sub_teachers'] = sub_col["teachers"]
        codes = ""
        for col in Subject.objects.filter(thread_id = thread_id).values("code"):
            codes += col["code"] + ", "
        context['sub_codes'] = codes[:-2]

        return context


class AboutView(TemplateView):
    template_name = "board/About.html"

class TermsView(TemplateView):
    template_name = "board/Terms.html"

class PrivacyView(TemplateView):
    template_name = "board/Privacy.html"

class SearchView(ListView):
    """検索画面に新規投稿一覧を表示する"""
    template_name = "board/Search.html"
    model = Post

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['post_list'] = self.model.objects.all().order_by('-created_at')[:5]

        # emergency ranking
        thread_dict = dict() # thread_dict[thread_id] = 非常事態数
        # post
        target_data = Post.objects.filter(emotion=0)
        groupby_data = target_data.values("thread_id").annotate(total=Count("thread_id"))
        for col in groupby_data:
            thread_dict[col["thread_id"]] = col["total"]
        # reply
        target_data = Reply.objects.filter(emotion=0)
        groupby_data = target_data.values("post_id").annotate(total=Count("post_id"))
        for col in groupby_data:
            thread_id = Post.objects.filter(post_id=col["post_id"]).values("thread")[0]["thread"]
            if thread_id in thread_dict.keys():
                thread_dict[thread_id] += col["total"]
            else:
                thread_dict[thread_id] = col["total"]
        
        ranking = []
        ranking_nums = sorted(thread_dict.items(), key=lambda x:x[1], reverse=True)[:5]
        for tid , num  in ranking_nums:
            title = Thread.objects.filter(pk=tid).values("title")[0]["title"]
            ranking.append(
                (tid, title, num)
            )

        context["ranking"] = ranking

        # Notice
        notice = Notice.objects.filter(is_show=True).order_by('created_at').values("message")
        context["notice"] = notice

        return context

class NewQuestionsView(ListView):
    """新規投稿一覧を表示するページ"""
    template_name = "board/NewQuestions.html"
    model = Post

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['post_list'] = self.model.objects.all().order_by('-created_at')[:40]
        return context

class ServiceWorkerView(ListView):
    def get(self, request, *args, **kwargs):
        swjs = "importScripts('https://cdn.ampproject.org/sw/amp-sw.js');"
        swjs += "AMP_SW.init();"
        response = HttpResponse(swjs, content_type='application/javascript')
        return response

class GetAppView(TemplateView):
    template_name = "board/App.html"