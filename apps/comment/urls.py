from django.urls import path

from comment.views import   CommentsListApiView, CommentsCreateApiView, CommentsRetrieveUpdateDestroyApiView


urlpatterns=[
    path('list/<int:pk>/', CommentsListApiView.as_view()),  # List task's comments
    path('create/', CommentsCreateApiView.as_view()),  # create comments
    path('<int:pk>/', CommentsRetrieveUpdateDestroyApiView.as_view()),  # Crud comments

]