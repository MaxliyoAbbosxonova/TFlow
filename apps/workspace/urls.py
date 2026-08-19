from django.urls import path

from workspace.views import WorkspaceListCreateApiView, WorkspaceRetrieveApiView, TeamListCreateApiView, \
    W_MemberListApiView, W_MemberCreateApiView, TeamUpdateDestroyApiView

urlpatterns = [
    path('',WorkspaceListCreateApiView.as_view()),
    path('<int:pk>',WorkspaceRetrieveApiView.as_view()),
    path('teams/',TeamListCreateApiView.as_view()),
    path('teams/<int:pk>',TeamUpdateDestroyApiView.as_view()),
    path('w_members/<int:pk>',W_MemberListApiView.as_view()),
    path('w_members/',W_MemberCreateApiView.as_view())
]
