import json
import html
import urllib.parse

from django.shortcuts import render
from django.http import HttpResponse, Http404, HttpResponseRedirect
from .models import Notice, Post, Reply, Subject, Thread, Review, Tag, Textbooks
from django.shortcuts import redirect
from django.views.generic import TemplateView, ListView
from django.views.generic.edit import FormMixin
from .forms import ReviewForm
from django.contrib import messages
from django.db.models import Count, Avg
from django.urls import reverse_lazy

class Index(ListView):
    def get(self, request, *args, **kwargs):
        return redirect("search/")


class ThreadView(FormMixin, ListView):
    template_name = "board/Chat.html"
    model = Post
    form_class = ReviewForm
    #context_object_name = 'post_data'
    ordering = ['-created_at']

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        thread_id = self.kwargs['thread_id']
        try:
            thread = Thread.objects.get(id = thread_id)
        except Thread.DoesNotExist:
            raise Http404()

        # スレッド情報
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

        # レビュー
        reviews = Review.objects.filter(thread_id = thread_id)
        context["review_count"] = reviews.count()
        context["review_is_enable"] = thread.enable_review

        ## 平均値を取得
        ratings_overall = reviews.aggregate(Avg('ratings_overall'))
        ratings_easiness = reviews.aggregate(Avg('ratings_easiness'))
        ratings_content = reviews.aggregate(Avg('ratings_content'))
        context.update(**ratings_overall, **ratings_easiness, **ratings_content)

        ## CSS用に.5刻みでoverallを計算 floatじゃないとうまくいかないので注意
        if ratings_overall['ratings_overall__avg'] is not None:
            context['ratings_overall_for_star'] = int(ratings_overall['ratings_overall__avg'] * 2) / 2.0
        else:
            context['ratings_overall_for_star'] = 0.0

        ## コメント
        comments = reviews.exclude(comment='').order_by('-created_at').values('comment')
        if len(comments) > 2:
            context['review_recent_comments'] = comments[:2]
            context['review_more_comments'] = comments[2:]
        else:
            context['review_recent_comments'] = comments
            context['review_more_comments'] = []

        ## タグ
        tags = []
        for row in reviews.values("tags").annotate(count=Count('id')):
            if row["tags"] is not None:
                name = Tag.objects.filter(id= row["tags"]).values("name")[0]["name"]
                count = row["count"]
                tags.append({"name" : name, "count" : count})

        tags.sort(key=lambda x: x['count'], reverse=True) # descending order
        context["review_tags"] = tags

        ## 教科書情報
        safe_html = ""
        try:
            textbooks_records = Textbooks.objects.filter(thread_id = thread_id).values()[0]
            textbooks = json.loads(textbooks_records["textbooks_json_object"])
            for row in textbooks["rows"]:
                for block in row["row"]:
                    if block["is_link"]:
                        safe_html += self.__create_amazon_link(block["text"])
                    else:
                        safe_html += html.escape(block["text"])
                safe_html += "<br>"
            safe_html = safe_html[:-4]
        except:
            safe_html = ""
        finally:
            if safe_html != "":
                context["textbooks"] = safe_html
            else:
                context["textbooks"] = "この科目の教科書情報は提供されていません。"
        return context

    def __create_amazon_link(self, target):
        html_escaped = html.escape(target)
        uri_escaped = urllib.parse.quote(target)
        link = f'<a class="textbook-link" target="_blank" href="https://www.amazon.co.jp/gp/search?ie=UTF8&tag=aplustsukub08-22&index=books&keywords={uri_escaped}">{html_escaped}</a>'
        return link

    def post(self, request, *args, **kwargs):
        self.object_list = self.get_queryset()
        form = self.get_form()
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def form_valid(self, form):
        review = form.save(commit=False)
        review.thread_id = self.kwargs['thread_id']
        review.save()
        form.save_m2m()
        messages.success(self.request, "この度はレビューしていただきありがとうございます。") 
        # もう一度元のページに戻る
        return HttpResponseRedirect(reverse_lazy(
            "threads", kwargs={"thread_id": self.kwargs["thread_id"]}
        ))
    def form_invalid(self, form):
        response = super().form_invalid(form)
        messages.error(self.request, "レビューの投稿に失敗しました。")
        return response
    
class ThreadViewBySubcode(ListView):
    """科目コードからスレッドにリダイレクトを行う e.g. /threads/codes/GC13201"""
    def get(self, request, *args, **kwargs):
        subcode = self.kwargs['subcode']
        try:
            # FYI: MySQLでは大文字小文字を区別しない
            thread_id = Subject.objects.filter(code = subcode).order_by("-year").values("thread_id")[0]["thread_id"]
        except IndexError:
            raise Http404()
        return redirect("threads", thread_id=thread_id)
        

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
        
        # Review
        review_list = Review.objects.all().select_related('thread').order_by('-created_at')[:3]
        context["review_list"] = review_list

        # UserAgent
        ua = self.request.META['HTTP_USER_AGENT']
        context["is_flutter_app"] =  (ua == "A+Tsukuba-flutter-App")

        return context

class NewQuestionsView(ListView):
    """新規投稿一覧を表示するページ"""
    template_name = "board/NewQuestions.html"
    model = Post

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context['post_list'] = self.model.objects.all().order_by('-created_at')[:40]
        return context

class GetAppView(TemplateView):
    template_name = "board/App.html"