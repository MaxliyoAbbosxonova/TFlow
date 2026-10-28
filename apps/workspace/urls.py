from django.urls import path
from workspace.views import (
    ChangeOwnerApiView,
    CheckTokenApiView,
    InvitationAcceptApiView,
    InvitationCreateApiView,
    RemoveWorkspaceMemberView,
    WMemberCreateApiView,
    WMembersListApiView,
    WorkspaceListCreateApiView,
    WorkspaceRetrieveApiView,
    WorkspaceRetrieveLISTApiView,
    WProjectsListApiView,
    WTeamsListApiView,
)

urlpatterns = [
    path('', WorkspaceListCreateApiView.as_view(), name='workspace-list-create'),
    path('list/user', WorkspaceRetrieveLISTApiView.as_view(), name='workspace-list-user'),
    path('<int:pk>', WorkspaceRetrieveApiView.as_view(), name='workspace-detail'),

    path('<int:pk>/members', WMembersListApiView.as_view(), name='workspace-members'),
    path('<int:pk>/projects', WProjectsListApiView.as_view(), name='workspace-projects'),
    path('<int:pk>/teams', WTeamsListApiView.as_view(), name='workspace-teams'),

    path('w_members/<int:pk>', WMemberCreateApiView.as_view(), name='workspace-member-create'),
    path("workspace-members/<int:member_id>/workspace/<int:w_space_id>/remove/",
         RemoveWorkspaceMemberView.as_view(), name='workspace-remove-member'),
    path('change_owner/<int:workspace_id>/<int:member_id>',
         ChangeOwnerApiView.as_view(), name='workspace-change-owner'),
    path('send_invitation/', InvitationCreateApiView.as_view(), name='workspace-invitation-create'),
    path('invitations/<uuid:token>/', CheckTokenApiView.as_view(), name='workspace-check-token'),
    path('invitations/<uuid:token>/accept', InvitationAcceptApiView.as_view(), name='workspace-invitation-accept'),
]
