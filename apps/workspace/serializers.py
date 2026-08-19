from rest_framework.serializers import ModelSerializer, ListSerializer

from shared.utils import RecursiveField
from workspace.models import Team, Project, Task, WorkspaceMember, Workspace


class TeamModelSerializer(ModelSerializer):
    class Meta:
        model = Team
        fields = "__all__"


class ProjectModelSerializer(ModelSerializer):
    class Meta:
        model = Project
        fields = "__all__"


class TaskModelSerializer(ModelSerializer):
    children = ListSerializer(child=RecursiveField(), source='get_children', read_only=True)

    class Meta:
        model = Task
        fields = "__all__"


class W_MembersModelSerializers(ModelSerializer):
    class Meta:
        model = WorkspaceMember
        fields = '__all__'


class WorkspaceModelSerializer(ModelSerializer):
    class Meta:
        model = Workspace
        fields = '__all__'


class WorkspaceMembersModelSerializer(ModelSerializer):
    members = W_MembersModelSerializers(many=True)

    class Meta:
        model = Workspace
        fields = ('id','members')

