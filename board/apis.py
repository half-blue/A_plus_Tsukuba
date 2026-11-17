from rest_framework.generics import ListAPIView, ListCreateAPIView
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import NotFound, MethodNotAllowed, PermissionDenied
from .serializers import *
from .models import Post, Thread, Reply, Review
from . import recaptcha
from django.db.models import Avg
from django.db.models import Q

class get_subthreads(ListAPIView):
    serializer_class = GetPostSerializer

    def get_queryset(self):
        thread_id = self.request.query_params.get("thread_id")
        return Post.objects.filter(thread_id = thread_id).order_by('-created_at')

class get_replies(ListAPIView):
    serializer_class = GetReplySerializer

    def get_queryset(self):
        post_id = self.request.query_params.get("post_id")
        return Reply.objects.filter(post_id = post_id).order_by('created_at')

class search_subjects(ListAPIView):
    serializer_class = SearchSubjectSerializer

    def get_queryset(self):
        q :str = self.request.query_params.get("q", "")
        return Subject.objects.filter(Q(name__icontains = q) | Q(code__startswith = q) | Q(schools__icontains = q) | Q(colleges__icontains = q)).order_by('code')[:500]

class RecaptchaProtectedCreateMixin:
    """入力が正しい投稿だけを reCAPTCHA で確かめ、点数と一緒に保存する (board/recaptcha.py)。
    入力の誤りで断る投稿には評価を作らない (評価の数だけ課金されるため)。
    点数 (recaptcha_score) はシリアライザーの fields に入れていないので、クライアントからは書けない"""
    recaptcha_action = None

    def perform_create(self, serializer):
        token = recaptcha.token_from(self.request.data)
        verdict = recaptcha.verify(self.request, token, self.recaptcha_action)
        if not verdict.allowed:
            raise PermissionDenied(recaptcha.REJECTED_MESSAGE)
        serializer.save(recaptcha_score=verdict.score)

class post_subthreads(RecaptchaProtectedCreateMixin, ListCreateAPIView):
    serializer_class = PostPostSerializer
    queryset = Post.objects.all()
    recaptcha_action = recaptcha.ACTION_POST_QUESTION

class post_replies(RecaptchaProtectedCreateMixin, ListCreateAPIView):
    queryset = Reply.objects.all()
    serializer_class = PostReplySerializer
    recaptcha_action = recaptcha.ACTION_POST_REPLY

class get_subject_scores(APIView):

    def get(self, request, subcode, format=None):
        """
        Return 3 scores of specified subcode
        """
        
        # 教科が存在するか確認
        try:
            ## FYI: MySQLでは大文字小文字を区別しない(照合順序によるけど)
            subject = Subject.objects.filter(code = subcode).order_by("-year")[0]
        except IndexError:
            raise NotFound("No such subject code")
        
        # レビューが無効化されている場合はエラーを返す
        if not subject.thread_id.enable_review:
            raise MethodNotAllowed("GET", detail="Reviews are disabled for this subject")

        # レビューを取得
        thread_id = subject.thread_id.id
        reviews = Review.objects.filter(thread_id = thread_id)

        # レビューが存在しない場合はNoneを返す
        count_ratings = reviews.count()
        if count_ratings == 0:
            serializer =  GetSubjectScoresSerializer(
                {
                    "subcode" : subcode,
                    "average_ratings_overall": None,
                    "average_ratings_easiness": None,
                    "average_ratings_content": None,
                    "count_ratings": 0,
                }
            )
            return Response(serializer.data)
        
        # 平均値を取得
        average_ratings = reviews.aggregate(Avg('ratings_overall'), Avg('ratings_easiness'), Avg('ratings_content'))
        serializer =  GetSubjectScoresSerializer(
                {
                    "subcode" : subcode,
                    "average_ratings_overall": average_ratings["ratings_overall__avg"],
                    "average_ratings_easiness": average_ratings["ratings_easiness__avg"],
                    "average_ratings_content": average_ratings["ratings_content__avg"],
                    "count_ratings": count_ratings,
                }
            )
        return Response(serializer.data)