from rest_framework.serializers import ModelSerializer

from project.models import Project
from task.serializers import TaskModelSerializer


class ProjectModelSerializer(ModelSerializer):
    class Meta:
        model = Project
        fields = "__all__"


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
