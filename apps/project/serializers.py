from project.models import Project
from rest_framework.exceptions import PermissionDenied
from rest_framework.serializers import ModelSerializer
from task.serializers import TaskModelSerializer
from workspace.models import WorkspaceMember


class ProjectModelSerializer(ModelSerializer):
    class Meta:
        model = Project
        fields = "__all__"

    def validate_workspace(self, ws):
        user = self.context["request"].user

        if user.is_staff:  # admin
            return ws
        if ws is None:
            raise PermissionDenied("Workspace ko'rsatilishi shart.")
        if ws.owner_id == user.id:  # owner
            return ws

        is_manager = WorkspaceMember.objects.filter(
            user=user,
            workspace=ws,
            role__in=[
                WorkspaceMember.Role.WORKSPACE_OWNER,
                WorkspaceMember.Role.MANAGER,
                WorkspaceMember.Role.ADMIN,
            ],
        ).exists()  # manager / admin roli
        if not is_manager:
            raise PermissionDenied("Bu workspace'da project yarata olmaysiz.")
        return ws


class ProjectsTasksModelSerializer(ModelSerializer):
    tasks = TaskModelSerializer(many=True)

    class Meta:
        model = Project
        fields = ('id', 'tasks')


class ProjectSerializer(ModelSerializer):
    tasks = TaskModelSerializer(many=True)

    class Meta:
        model = Project
        fields = ("id", 'title', 'tasks')


class ProjectsForTeamsSerializer(ModelSerializer):
    class Meta:
        model = Project
        fields = ("id", 'title')
