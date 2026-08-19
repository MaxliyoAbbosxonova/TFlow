from rest_framework.generics import ListCreateAPIView, RetrieveAPIView, RetrieveUpdateDestroyAPIView

from shared.utils import UserPermission
from workspace.models import Workspace, Team, Project, WorkspaceMember
from workspace.serializers import WorkspaceModelSerializer, TeamModelSerializer, WorkspaceMembersModelSerializer, \
    ProjectModelSerializer, W_MembersModelSerializers


# Create your views here.

class WorkspaceListCreateApiView(ListCreateAPIView):
    serializer_class = WorkspaceModelSerializer

    def get_queryset(self):
        if self.request.user.is_superuser:
            return Workspace.objects.all()
        return Workspace.objects.filter(members__user=self.request.user)


class WorkspaceRetrieveApiView(RetrieveUpdateDestroyAPIView):
    queryset = Workspace.objects.all()
    serializer_class = WorkspaceModelSerializer


class TeamListCreateApiView(ListCreateAPIView):
    queryset = Team.objects.all()
    serializer_class = TeamModelSerializer
    permission_classes = (UserPermission,)

class TeamUpdateDestroyApiView(RetrieveUpdateDestroyAPIView):
    queryset = Team.objects.all()
    serializer_class = TeamModelSerializer



class W_MemberListApiView(RetrieveAPIView):
    queryset = Workspace.objects.all()
    serializer_class = WorkspaceMembersModelSerializer

class W_MemberCreateApiView(ListCreateAPIView):
    queryset = WorkspaceMember.objects.all()
    serializer_class = W_MembersModelSerializers



class ProjectListCreateApiView(ListCreateAPIView):
    queryset = Project.objects.all()
    serializer_class =ProjectModelSerializer