from rest_framework.generics import ListAPIView, ListCreateAPIView
from .serializers import *
from .models import Post, Thread, Reply
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

class post_subthreads(ListCreateAPIView):
    serializer_class = PostPostSerializer
    queryset = Post.objects.all()

class post_replies(ListCreateAPIView):
    queryset = Reply.objects.all()
    serializer_class = PostReplySerializer
