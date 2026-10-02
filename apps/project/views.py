from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema
from rest_framework.filters import SearchFilter
from rest_framework.generics import RetrieveAPIView, RetrieveUpdateDestroyAPIView, CreateAPIView, ListAPIView
from rest_framework.pagination import LimitOffsetPagination

from project.models import Project
from project.serializers import ProjectModelSerializer, ProjectsTasksModelSerializer
from shared.permissions import Workspace_Projects_Members, Projects_Tasks_Members
from task.models import Task
from task.serializers import TaskModelSerializer


# Create your views here.


# Bo'ldi v
@extend_schema(tags=["Projects"])
class ProjectCreateApiView(CreateAPIView):
    serializer_class = ProjectModelSerializer
    permission_classes = (Workspace_Projects_Members,)
    queryset = Project.objects.all()


# Bo'ldi v
@extend_schema(tags=["Projects"])
class ProjectRetrieveUpdateDestroyApiView(RetrieveUpdateDestroyAPIView):
    serializer_class = ProjectModelSerializer
    permission_classes = (Workspace_Projects_Members,)
    queryset = Project.objects.all()

@extend_schema(tags=["Projects"])
class Tasks_by_Project(ListAPIView):
    serializer_class = TaskModelSerializer
    permission_classes = (Projects_Tasks_Members,)
    pagination_class = LimitOffsetPagination

    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['assignee', 'status', 'priority', 'label',
                        'deadline', 'created_at']
    search_fields = ['title', 'description']

    def get_queryset(self):
        return Task.objects.filter(project_id=self.kwargs['pk'])