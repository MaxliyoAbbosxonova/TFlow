from comment.views import (
    CommentsCreateApiView,
    CommentsListApiView,
    CommentsRetrieveUpdateDestroyApiView,
    ReplyToComment,
)
from django.urls import path

urlpatterns = [
    path('task_comments/<int:task_id>/', CommentsListApiView.as_view(), name='comments-list'),
    path('create/', CommentsCreateApiView.as_view(), name='comments-create'),
    path('my_comments/<int:pk>/', CommentsRetrieveUpdateDestroyApiView.as_view(), name='comments-detail'),
    path('reply/', ReplyToComment.as_view(), name='comments-reply'),
]
