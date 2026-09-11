from django.urls import path

from project.views import ProjectCreateApiView, ProjectRetrieveUpdateDestroyApiView, \
    Tasks_by_Project

urlpatterns = [
    path('<int:pk>/tasks', Tasks_by_Project.as_view()),  # tasks_by projects
    path('', ProjectCreateApiView.as_view()),  # projects list
    path('<int:pk>/', ProjectRetrieveUpdateDestroyApiView.as_view()),  # Projects CRUD

]
