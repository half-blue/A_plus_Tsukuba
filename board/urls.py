from django.urls import path

from . import views
from . import apis

urlpatterns = [
    path('', views.Index.as_view(), name='index'),
    path('threads/<int:thread_id>/', views.ThreadView.as_view(), name='threads'),
    path('api/get_subthreads', apis.get_subthreads.as_view(), name = "api_get_subthreads"),
    path('api/get_replies', apis.get_replies.as_view(), name = "api_get_replies"),
]