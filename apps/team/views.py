from drf_spectacular.utils import extend_schema
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView, get_object_or_404, RetrieveAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from shared.permissions import Projects_Tasks_Members
from team.models import Team
from team.serializers import TeamModelSerializer, TeamsProjectsModelSerializer
from workspace.models import WorkspaceMember


# Create your views here.


# Bo'ldi v
@extend_schema(tags=["Teams"])
class TeamListCreateApiView(ListCreateAPIView):
    queryset = Team.objects.all()
    serializer_class = TeamModelSerializer

    def has_permission(self, request):
        if request.method == "GET":
            return request.user.is_staff
        elif request.method == "POST" or request.method == "PATCH" or request.method == "PUT":
            if ((Team.workspace.owner or Team.team_lead) is WorkspaceMember.objects.filter(
                    user=self.request.user)) or self.request.user.is_staff:
                return True
        return None


# Bo'ldi v
@extend_schema(tags=["Teams"])
class AddTeamMemberView(APIView):

    def post(self, request, member_id, team_id):
        member = get_object_or_404(WorkspaceMember, id=member_id)
        team = get_object_or_404(Team, id=team_id)

        if team.workspace_id != member.workspace_id:
            return Response(
                {"detail": "Team boshqa workspace'ga tegishli."},
                status=400
            )
        member.team.add(team)

        return Response({"detail": "Member Teamga qo'shildi ."})


# Bo'ldi v
@extend_schema(tags=["Teams"])
class RemoveTeamMemberView(APIView):

    def has_permission(self, request):
        if request.method == "GET":
            return request.user.is_staff
        elif request.method == "POST" or request.method == "PATCH" or request.method == "PUT":
            if ((Team.workspace.owner or Team.team_lead) is WorkspaceMember.objects.filter(
                    user=self.request.user)) or self.request.user.is_staff:
                return True
        return None

    def delete(self, request, member_id, team_id):
        member = get_object_or_404(WorkspaceMember, id=member_id)
        team = get_object_or_404(Team, id=team_id)

        if team.workspace_id != member.workspace_id:
            return Response(
                {"detail": "Team boshqa workspace'ga tegishli."},
                status=400
            )
        member.team.remove(team)

        return Response({"detail": "Member endi Team a'zosi emas."})


# Bo'ldi v
@extend_schema(tags=["Teams"])
class TeamUpdateDestroyApiView(RetrieveUpdateDestroyAPIView):
    queryset = Team.objects.all()
    serializer_class = TeamModelSerializer


@extend_schema(tags=["Teams"])
class Project_by_Teams(RetrieveAPIView):
    queryset = Team.objects.all()
    serializer_class = TeamsProjectsModelSerializer
    permission_classes = (Projects_Tasks_Members,)


@extend_schema(tags=["Teams"])
class Tasks_by_Teams(RetrieveAPIView):
    queryset = Team.objects.all()
    serializer_class = TeamsProjectsModelSerializer
    permission_classes = (Projects_Tasks_Members,)
