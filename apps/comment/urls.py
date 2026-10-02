from django.urls import path

from comment.views import   CommentsListApiView, CommentsCreateApiView, CommentsRetrieveUpdateDestroyApiView


urlpatterns=[
    path('task_comments/<int:task_id>/', CommentsListApiView.as_view()),  # List task's comments
    path('create/', CommentsCreateApiView.as_view()),  # create comments
    path('my_comments/<int:pk>/', CommentsRetrieveUpdateDestroyApiView.as_view()),  # Crud comments

]