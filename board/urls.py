from django.urls import path

from . import views
from . import apis

urlpatterns = [
    path('', views.Index.as_view(), name='index'),
    path('threads/<int:thread_id>/', views.ThreadView.as_view(), name='threads'),
    path('search/', views.SearchView.as_view(), name='search'),
    path('search/new_questions/', views.NewQuestionsView.as_view(), name='new_questions'),
    path('api/get_subthreads', apis.get_subthreads.as_view(), name = "api_get_subthreads"),
    path('api/get_replies', apis.get_replies.as_view(), name = "api_get_replies"),
    path('api/post_subthreads', apis.post_subthreads.as_view(), name = "api_post_subthreadss"),
    path('api/post_replies', apis.post_replies.as_view(), name = "api_post_replies"),
    path('api/search_subjects', apis.search_subjects.as_view(), name = "api_search_subjects"),
    path('about/', views.AboutView.as_view(), name = "about"),
    path('terms/', views.TermsView.as_view(), name = "terms"),
    path('privacy/', views.PrivacyView.as_view(), name = "privacy"),
]