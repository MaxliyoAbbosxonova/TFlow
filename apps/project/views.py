from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema
from project.models import Project
from project.serializers import ProjectModelSerializer
from rest_framework.filters import SearchFilter
from rest_framework.generics import (
    CreateAPIView,
    ListAPIView,
    RetrieveUpdateDestroyAPIView,
)
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import IsAuthenticated
from shared.permissions import (
    ProjectOwnerOrManager,
    ProjectsTasksMembers,
)
from task.models import Task
from task.serializers import TaskModelSerializer

# Create your views here.


# Bo'ldi v
@extend_schema(tags=["Projects"])
class ProjectCreateApiView(CreateAPIView):
    serializer_class = ProjectModelSerializer
    permission_classes = (IsAuthenticated,)
    queryset = Project.objects.all()


# Bo'ldi v
@extend_schema(tags=["Projects"])
class ProjectRetrieveUpdateDestroyApiView(RetrieveUpdateDestroyAPIView):
    serializer_class = ProjectModelSerializer
    permission_classes = (ProjectOwnerOrManager,)
    queryset = Project.objects.all()


@extend_schema(tags=["Projects"])
class TasksByProject(ListAPIView):
    serializer_class = TaskModelSerializer
    permission_classes = (ProjectsTasksMembers,)
    pagination_class = LimitOffsetPagination

    filter_backends = [DjangoFilterBackend, SearchFilter]
    filterset_fields = ['assignee', 'status', 'priority', 'label',
                        'deadline', 'created_at']
    search_fields = ['title', 'description']

    def get_queryset(self):
        return Task.objects.filter(project_id=self.kwargs['pk'])
