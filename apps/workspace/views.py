from drf_spectacular.utils import extend_schema, PolymorphicProxySerializer
from rest_framework.generics import ListCreateAPIView, RetrieveAPIView, RetrieveUpdateDestroyAPIView, get_object_or_404, \
    ListAPIView
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK
from rest_framework.views import APIView

from services.invitation import create_invitation
from services.workspace import Invitation_Accept, Invitation_Anonymouse_Accept
from shared.permissions import Workspace_Projects_Members, IsOwnerManagerAdmin, IsOwnerManagerAdminForLISTTEAMS
from workspace.models import Workspace, WorkspaceMember
from workspace.serializers import WorkspaceModelSerializer, WorkspaceMembersModelSerializer, \
    WorkspaceProjectsModelSerializer, \
    WorkspaceMembersModelSerializers, WorkspaceInvitationModelSerializer, CheckTokenSerializer, \
    InvitationAcceptModelSerializer, InvitationAnonymousAcceptModelSerializer, WorkspaceTeamsModelSerializer
from workspace.tasks import send_invitation_accept_email_task


# Create your views here.
# Bo'ldi v
@extend_schema(tags=["Workspace"])
class WorkspaceListCreateApiView(ListCreateAPIView):
    serializer_class = WorkspaceModelSerializer
    pagination_class=LimitOffsetPagination


    def get_queryset(self):
        if self.request.user.is_superuser:
            return Workspace.objects.all()

@extend_schema(tags=["Workspace"])
class WorkspaceRetrieveLISTApiView(ListAPIView):
    serializer_class = WorkspaceModelSerializer
    def get_queryset(self):
        workspace=Workspace.objects.filter(owner=self.request.user).all()
        if workspace:
            return workspace
        return Response(data='sizda wspace yoq')





# Bo'ldi v
@extend_schema(tags=["Workspace"])
class WorkspaceRetrieveApiView(RetrieveUpdateDestroyAPIView):
    queryset = Workspace.objects.all()
    serializer_class = WorkspaceModelSerializer
    permission_classes =(IsOwnerManagerAdminForLISTTEAMS,)



@extend_schema(tags=["Workspace"])
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
        if not user_.workspace.id==workspace_id:
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

    def delete(self, request, member_id, w_space_id):
        member = get_object_or_404(
            WorkspaceMember,
            id=member_id
        )

        if not member.workspace_id == w_space_id:
            return Response(
                {"detail": "Member boshqa workspace'ga tegishli."},
                status=400
            )
        WorkspaceMember.objects.filter(id=member_id).delete()
        return Response(
            {"detail": "Member workspace'dan chiqarildi."},
            status=200
        )


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


@extend_schema(tags=["Workspace"])
class W_TeamsListApiView(RetrieveAPIView):
    queryset = Workspace.objects.all()
    serializer_class = WorkspaceTeamsModelSerializer
    permission_classes = (IsOwnerManagerAdminForLISTTEAMS,)


# bitmagan
@extend_schema(tags=["WorkspaceMember"])
class W_MemberCreateApiView(ListCreateAPIView):
    queryset = WorkspaceMember.objects.all()
    serializer_class = WorkspaceMembersModelSerializers


@extend_schema(tags=['Workspace'])
class InvitationCreateApiView(APIView):
    serializer_class = WorkspaceInvitationModelSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        invitation = create_invitation(serializer.validated_data)

        return Response({'detail': "invitation sended", 'data': invitation.email}, status=HTTP_200_OK)


@extend_schema(tags=['Workspace'])
class CheckTokenApiView(APIView):
    serializer_class = CheckTokenSerializer

    def get(self, request, token):
        serializer = self.serializer_class(data={'token': token})
        serializer.is_valid(raise_exception=True)
        return Response({'data': serializer.validated_data
                         }, status=HTTP_200_OK)

@extend_schema(tags=['Workspace'])
class InvitationAcceptApiView(APIView):
    permission_classes = (AllowAny,)

    @extend_schema(
        request=PolymorphicProxySerializer(
            component_name='InvitationAcceptRequest',
            serializers=[
                InvitationAcceptModelSerializer,  # tizimga kirgan uchun
                InvitationAnonymousAcceptModelSerializer,  # kirmagan uchun
            ],
            resource_type_field_name=None,  # bizda "type" degan ajratuvchi field yo'q
        ),
        responses={200: dict},  # yoki mos response serializer
        description=(
                "Taklifni qabul qilish. Agar foydalanuvchi tizimga kirgan bo'lsa, "
                "faqat `token` yuboriladi. Kirmagan bo'lsa — `token, email, phone, "
                "password, profile` yuborilishi shart."
        ),
    )
    def post(self, request, token):
        if request.user.is_authenticated:
            serializer = InvitationAcceptModelSerializer(data={**request.data, 'token': token},
                                                         context={'request': request})
            serializer.is_valid(raise_exception=True)

            member = Invitation_Accept(serializer.validated_data)
            send_invitation_accept_email_task(member)
            return Response({
                'detail': 'Taklif qabul qilindi. Siz endi workspace a\'zosisiz.',
                'workspace_id': member.workspace_id,
                'role': member.role,
            }, status=HTTP_200_OK)
        else:
            serializer = InvitationAnonymousAcceptModelSerializer(data={**request.data, 'token': token},
                                                                  context={'request': request})
            serializer.is_valid(raise_exception=True)
            member = Invitation_Anonymouse_Accept(serializer.validated_data)
            send_invitation_accept_email_task(member)
            return Response({
                'detail': 'Taklif qabul qilindi. Siz endi workspace a\'zosisiz.',
                'workspace_id': member.workspace_id,
                'role': member.role,
            }, status=HTTP_200_OK)
