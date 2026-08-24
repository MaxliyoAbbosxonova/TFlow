from django.db import transaction
from rest_framework import serializers
from rest_framework.serializers import ModelSerializer, ListSerializer

from shared.utils import RecursiveField
from workspace.models import Team, Project, Task, WorkspaceMember, Workspace


class TeamModelSerializer(ModelSerializer):
    class Meta:
        model = Team
        fields = "__all__"

    def create(self, validated_data):
        with transaction.atomic():
            team_lead = validated_data['team_lead']
            workspace = validated_data['workspace']
            team = Team.objects.create(**validated_data)
            WorkspaceMember(user=team_lead, workspace=workspace).role = WorkspaceMember.Role.TEAM_LEAD
        return team


class TaskAdminModelSerializer(ModelSerializer):
    children = ListSerializer(child=RecursiveField(), source='get_children', read_only=True)

    class Meta:
        model = Task
        fields = "__all__"


class WorkspaceMembersModelSerializers(ModelSerializer):
    class Meta:
        model = WorkspaceMember
        fields = '__all__'


class WorkspaceModelSerializer(ModelSerializer):
    class Meta:
        model = Workspace
        fields = '__all__'

    def create(self, validated_data):
        with transaction.atomic():
            owner = validated_data.pop("owner")

            workspace = Workspace.objects.create(
                owner=owner,
                **validated_data
            )

            member = WorkspaceMember.objects.create(
                user=owner,
                role=WorkspaceMember.Role.WORKSPACE_OWNER
            )

            member.workspace.add(workspace)

            return workspace


class WorkspaceMembersModelSerializer(ModelSerializer):
    members = WorkspaceMembersModelSerializers(many=True)

    class Meta:
        model = Workspace
        fields = ('id', 'members')


class ProjectModelSerializer(ModelSerializer):
    class Meta:
        model = Project
        fields = "__all__"


class WorkspaceProjectsModelSerializer(ModelSerializer):
    products = ProjectModelSerializer(many=True)

    class Meta:
        model = Workspace
        fields = ('id', 'products')


class TaskModelSerializer(ModelSerializer):
    children = ListSerializer(child=RecursiveField(), source='get_children', read_only=True)

    class Meta:
        model = Task
        fields = "__all__"
