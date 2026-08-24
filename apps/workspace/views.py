from drf_spectacular.utils import extend_schema
from rest_framework.generics import ListCreateAPIView, RetrieveAPIView, RetrieveUpdateDestroyAPIView, get_object_or_404, \
    CreateAPIView
from rest_framework.parsers import FileUploadParser, MultiPartParser, FormParser
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from shared.utils import Workspace_Projects_Members
from workspace.models import Workspace, Team, WorkspaceMember, Project, Task
from workspace.serializers import WorkspaceModelSerializer, TeamModelSerializer, WorkspaceMembersModelSerializer, \
    ProjectModelSerializer, WorkspaceProjectsModelSerializer, \
    WorkspaceMembersModelSerializers, TaskModelSerializer, TaskAdminModelSerializer


# Create your views here.
# Bo'ldi v
@extend_schema(tags=["Workspace"])
class WorkspaceListCreateApiView(ListCreateAPIView):
    serializer_class = WorkspaceModelSerializer

    def get_queryset(self):
        if self.request.user.is_superuser:
            return Workspace.objects.all()
        return Workspace.objects.filter(members__user=self.request.user)


# Bo'ldi v
@extend_schema(tags=["Workspace"])
class WorkspaceRetrieveApiView(RetrieveUpdateDestroyAPIView):
    queryset = Workspace.objects.all()
    serializer_class = WorkspaceModelSerializer


class ChangeOwnerApiView(APIView):

    def post(self, request, workspace_id, member_id):
        workspace = get_object_or_404(
            Workspace,
            id=workspace_id
        )

        user_ = get_object_or_404(
            WorkspaceMember,
            id=member_id
        )

        if not workspace.owner == request.user:
            return Response(
                {"detail": "Workspace boshqa User'ga tegishli."},
                status=400
            )
        if not user_.workspace.filter(id=workspace_id).exists():
            return Response(
                {"detail": "Bu user ushbu workspace a'zosi emas."},
                status=400
            )
        workspace.owner = user_.user
        workspace.save()

        return Response(
            {"detail": "Workspace owneri almashtirildi."},
            status=200
        )


# Bo'ldi v
@extend_schema(tags=["Workspace"])
class RemoveWorkspaceMemberView(APIView):

    def post(self, request, member_id, w_space_id):
        member = get_object_or_404(
            WorkspaceMember,
            id=member_id
        )

        workspace = get_object_or_404(
            Workspace,
            id=w_space_id
        )

        if not member.workspace.filter(id=w_space_id).exists():
            return Response(
                {"detail": "Member boshqa workspace'ga tegishli."},
                status=400
            )

        member.workspace.remove(workspace)

        return Response(
            {"detail": "Member workspace'dan chiqarildi."},
            status=200
        )


# Bo'ldi v
@extend_schema(tags=["Team"])
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
@extend_schema(tags=["Team"])
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
@extend_schema(tags=["Team"])
class RemoveTeamMemberView(APIView):

    def has_permission(self, request):
        if request.method == "GET":
            return request.user.is_staff
        elif request.method == "POST" or request.method == "PATCH" or request.method == "PUT":
            if ((Team.workspace.owner or Team.team_lead) is WorkspaceMember.objects.filter(
                    user=self.request.user)) or self.request.user.is_staff:
                return True
        return None

    def post(self, request, member_id, team_id):
        member = get_object_or_404(WorkspaceMember, id=member_id)
        team = get_object_or_404(Team, id=team_id)

        if team.workspace_id != member.workspace_id:
            return Response(
                {"detail": "Team boshqa workspace'ga tegishli."},
                status=400
            )
        member.team.remove(team)

        return Response({"detail": "Member Teamga qo'shildi ."})


# Bo'ldi v
@extend_schema(tags=["Team"])
class TeamUpdateDestroyApiView(RetrieveUpdateDestroyAPIView):
    queryset = Team.objects.all()
    serializer_class = TeamModelSerializer


# Bo'ldi v
@extend_schema(tags=["WorkspaceMember"])
class W_MembersListApiView(RetrieveAPIView):
    queryset = Workspace.objects.all()
    serializer_class = WorkspaceMembersModelSerializer
    permission_classes = (Workspace_Projects_Members,)


# Bo'ldi v
@extend_schema(tags=["Workspace"])
class W_ProjectsListApiView(RetrieveAPIView):
    queryset = Workspace.objects.all()
    serializer_class = WorkspaceProjectsModelSerializer
    permission_classes = (Workspace_Projects_Members,)


# bitmagan
@extend_schema(tags=["WorkspaceMember"])
class W_MemberCreateApiView(ListCreateAPIView):
    queryset = WorkspaceMember.objects.all()
    serializer_class = WorkspaceMembersModelSerializers


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


class TaskListApiView(ListCreateAPIView):
    serializer_class = TaskAdminModelSerializer
    queryset = Task.objects.all()
    permission_classes = (IsAdminUser,)
    parser_classes = [MultiPartParser, FormParser]

class TaskCreateApiView(CreateAPIView):
    serializer_class = TaskModelSerializer
    queryset = Task.objects.all()
    parser_classes = [MultiPartParser, FormParser]

    @extend_schema(
        request=TaskModelSerializer,
        responses=TaskModelSerializer,
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


