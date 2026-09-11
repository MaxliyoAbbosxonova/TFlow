from drf_spectacular.utils import extend_schema
from rest_framework.generics import RetrieveAPIView, RetrieveUpdateDestroyAPIView, CreateAPIView

from project.models import Project
from project.serializers import ProjectModelSerializer, ProjectsTasksModelSerializer
from shared.permissions import Workspace_Projects_Members, Projects_Tasks_Members


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
class Tasks_by_Project(RetrieveAPIView):
    queryset = Project.objects.all()
    serializer_class = ProjectsTasksModelSerializer
    permission_classes = (Projects_Tasks_Members,)
