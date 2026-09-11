from django.db import transaction
from rest_framework.serializers import ModelSerializer

from project.serializers import ProjectSerializer
from team.models import Team
from workspace.models import WorkspaceMember


class TeamsProjectsModelSerializer(ModelSerializer):
    projects = ProjectSerializer(many=True)

    class Meta:
        model = Team
        fields = ('id', 'projects')


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
