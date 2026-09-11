from django.urls import path
from rest_framework.views import APIView

from workspace.views import InvitationAcceptApiView
from workspace.views import WorkspaceListCreateApiView, WorkspaceRetrieveApiView, \
    W_MembersListApiView, W_MemberCreateApiView, \
    RemoveWorkspaceMemberView, W_ProjectsListApiView, \
    ChangeOwnerApiView, InvitationCreateApiView, CheckTokenApiView

urlpatterns = [
    path('', WorkspaceListCreateApiView.as_view()),
    path('<int:pk>', WorkspaceRetrieveApiView.as_view()),

    path('<int:pk>/members', W_MembersListApiView.as_view()),  # members by workspace
    path('<int:pk>/projects', W_ProjectsListApiView.as_view()),  # projects by workspace

    path('w_members/', W_MemberCreateApiView.as_view()),

    path(
        "workspace-members/<int:member_id>/workspace/<int:w_space_id>/remove/",
        RemoveWorkspaceMemberView.as_view(),  # remove member from W_space
    ),
    path('change_owner/<int:workspace_id>/<int:member_id>', ChangeOwnerApiView.as_view()),  # change w_space owner
    path('send_invitation/',InvitationCreateApiView.as_view()),
    path('invitations/<uuid:token>/',CheckTokenApiView.as_view()),
    path('invitations/<uuid:token>/accept',InvitationAcceptApiView.as_view())
]
