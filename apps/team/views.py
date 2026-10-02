from drf_spectacular.utils import extend_schema
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView, get_object_or_404, RetrieveAPIView
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from shared.permissions import Projects_Tasks_Members, IsOwnerManagerAdmin
from team.models import Team
from team.serializers import TeamModelSerializer, TeamsProjectsModelSerializer, TeamsTasksModelSerializer
from workspace.models import WorkspaceMember


# Create your views here.


# Bo'ldi v
@extend_schema(tags=["Teams"])
class TeamListCreateApiView(ListCreateAPIView):
    queryset = Team.objects.all()
    serializer_class = TeamModelSerializer
    permission_classes = (IsAdminUser,)
    pagination_class=LimitOffsetPagination




# Bo'ldi v
@extend_schema(tags=["Teams"])
class AddTeamMemberView(APIView):
    permission_classes = (IsOwnerManagerAdmin,)

    def post(self, request, member_id, pk):
        member = get_object_or_404(WorkspaceMember, id=member_id)
        team = get_object_or_404(Team, id=pk)

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
    permission_classes = (IsOwnerManagerAdmin,)


    def delete(self, request, member_id, pk):
        member = get_object_or_404(WorkspaceMember, id=member_id)
        team = get_object_or_404(Team, id=pk)

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
    permission_classes = (IsOwnerManagerAdmin,)


@extend_schema(tags=["Teams"])
class Project_by_Teams(RetrieveAPIView):
    queryset = Team.objects.all()
    serializer_class = TeamsProjectsModelSerializer
    permission_classes = (Projects_Tasks_Members,)
    pagination_class=LimitOffsetPagination



@extend_schema(tags=["Teams"])
class Tasks_by_Teams(RetrieveAPIView):
    serializer_class = TeamsTasksModelSerializer
    permission_classes = (Projects_Tasks_Members,)

    def get_queryset(self):
        return Team.objects.filter()

