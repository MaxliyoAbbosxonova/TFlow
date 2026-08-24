from django.urls import path

from workspace.views import WorkspaceListCreateApiView, WorkspaceRetrieveApiView, TeamListCreateApiView, \
    W_MembersListApiView, W_MemberCreateApiView, TeamUpdateDestroyApiView, AddTeamMemberView, RemoveTeamMemberView, \
    RemoveWorkspaceMemberView, ProjectCreateApiView, W_ProjectsListApiView, ProjectRetrieveUpdateDestroyApiView, \
    ChangeOwnerApiView, TaskCreateApiView, TaskListApiView

urlpatterns = [
    path('', WorkspaceListCreateApiView.as_view()),
    path('<int:pk>', WorkspaceRetrieveApiView.as_view()),
    path('teams/', TeamListCreateApiView.as_view()),
    path('teams/<int:pk>', TeamUpdateDestroyApiView.as_view()),
    path('<int:pk>/members', W_MembersListApiView.as_view()),
    path('<int:pk>/projects', W_ProjectsListApiView.as_view()),

    path('w_members/', W_MemberCreateApiView.as_view()),
    path(
        "workspace-members/<int:member_id>/teams/<int:team_id>/",
        AddTeamMemberView.as_view()
    ),

    path(
        "workspace-members/<int:member_id>/teams/<int:team_id>/remove/",
        RemoveTeamMemberView.as_view()
    ),
    path(
        "workspace-members/<int:member_id>/workspace/<int:w_space_id>/remove/",
        RemoveWorkspaceMemberView.as_view(),
    ), path('projects/', ProjectCreateApiView.as_view()),
    path('projects/<int:pk>', ProjectRetrieveUpdateDestroyApiView.as_view()),
    path('change_owner/<int:workspace_id>/<int:member_id>', ChangeOwnerApiView.as_view()),
    path('task/', TaskCreateApiView.as_view()),
    path('tasks/', TaskListApiView.as_view()),

]
