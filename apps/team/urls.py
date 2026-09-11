from django.urls import path

from team.views import TeamListCreateApiView, \
    TeamUpdateDestroyApiView, AddTeamMemberView, RemoveTeamMemberView, \
    Project_by_Teams, Tasks_by_Teams

urlpatterns = [
    path('list/', TeamListCreateApiView.as_view()),  # Teams List(admin) Create(all)
    path('<int:pk>/', TeamUpdateDestroyApiView.as_view()),  # teams CRUD
    path('<int:pk>/projects', Project_by_Teams.as_view()),  # projects by teams
    path('<int:pk>/tasks', Tasks_by_Teams.as_view()),  # projects by teams
    path(
        "team-members/<int:member_id>/teams/<int:team_id>/",
        AddTeamMemberView.as_view()  # add member to team
    ),
    path(
        "team-members/<int:member_id>/teams/<int:team_id>/remove/",
        RemoveTeamMemberView.as_view()  # remove member from team
    ),
]
