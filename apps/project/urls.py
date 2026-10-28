from django.urls import path
from project.views import (
    ProjectCreateApiView,
    ProjectRetrieveUpdateDestroyApiView,
    TasksByProject,
)

urlpatterns = [
    path('<int:pk>/tasks', TasksByProject.as_view(), name='project-tasks'),
    path('', ProjectCreateApiView.as_view(), name='project-create'),
    path('<int:pk>/', ProjectRetrieveUpdateDestroyApiView.as_view(), name='project-detail'),
]
