from django.urls import path
from team.views import (
    AddTeamMemberView,
    ProjectByTeams,
    RemoveTeamMemberView,
    TasksByTeams,
    TeamListCreateApiView,
    TeamUpdateDestroyApiView,
)

urlpatterns = [
    path('list/', TeamListCreateApiView.as_view()),  # Teams List(admin) Create(all)
    path('<int:pk>/', TeamUpdateDestroyApiView.as_view()),  # teams CRUD
    path('<int:pk>/projects', ProjectByTeams.as_view()),  # projects by teams
    path('<int:pk>/tasks', TasksByTeams.as_view()),  # projects by teams
    path(
        "team-members/<int:member_id>/teams/<int:pk>/",
        AddTeamMemberView.as_view()  # add member to team
    ),
    path(
        "team-members/<int:member_id>/teams/<int:pk>/remove/",
        RemoveTeamMemberView.as_view()  # remove member from team
    ),
]
