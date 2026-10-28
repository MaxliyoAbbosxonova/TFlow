import re

from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError
from rest_framework.fields import CharField, EmailField, UUIDField
from rest_framework.serializers import ModelSerializer, Serializer

from project.serializers import ProjectModelSerializer
from team.serializers import TeamModelSerializer
from users.serializers import ProfileModelSerializer, UserListForWorkspaceMembers
from workspace.models import Workspace, WorkspaceInvitation, WorkspaceMember


class WorkspaceMembersModelSerializers(ModelSerializer):
    user=UserListForWorkspaceMembers()
    class Meta:
        model = WorkspaceMember
        fields = ('team','user','role')


class WorkspaceModelSerializer(ModelSerializer):
    class Meta:
        model = Workspace
        fields = ('name', 'description', 'logo')

    def create(self, validated_data):
        request = self.context['request']

        with transaction.atomic():
            workspace = Workspace.objects.create(
                owner=request.user,
                **validated_data
            )

            WorkspaceMember.objects.create(
                user=request.user,
                workspace=workspace,
                role=WorkspaceMember.Role.WORKSPACE_OWNER,
            )

            return workspace


class WorkspaceMembersModelSerializer(ModelSerializer):
    members = WorkspaceMembersModelSerializers(many=True)

    class Meta:
        model = Workspace
        fields = ('id', 'members')


class WorkspaceProjectsModelSerializer(ModelSerializer):
    products = ProjectModelSerializer(many=True)

    class Meta:
        model = Workspace
        fields = ('id', 'products')


class WorkspaceTeamsModelSerializer(ModelSerializer):
    teams = TeamModelSerializer(many=True)

    class Meta:
        model = Workspace
        fields = ('id', 'teams')


class WorkspaceInvitationModelSerializer(ModelSerializer):
    class Meta:
        model = WorkspaceInvitation
        fields = ('workspace', 'email', 'role')

    def validate(self, validated_data):
        workspace = validated_data['workspace']
        request = self.context['request']
        member = WorkspaceMember.objects.filter(user=request.user, workspace=workspace).first()
        if member is None:
            raise ValidationError('Siz bu workspace a`zosi emassiz')
        validated_data['invited_by'] = member
        return validated_data


class CheckTokenSerializer(Serializer):
    token = UUIDField()

    def validate(self, validated_data):
        token = validated_data['token']
        invitation = WorkspaceInvitation.objects.filter(token=token).first()
        if not invitation:
            raise ValidationError(" Bunday Taklif havolasi mavjud emas ")
        if invitation.expires_at <= timezone.now():
            raise ValidationError(" Tokenning muddati o'tgan ")
        if invitation.status != WorkspaceInvitation.Status.PENDING:
            raise ValidationError('Token yaroqsiz ')

        validated_data['workspace'] = invitation.workspace.id
        validated_data['invited_by'] = invitation.invited_by.id
        validated_data['role'] = invitation.role
        validated_data['invitation'] = invitation.id

        return validated_data


class InvitationAnonymousAcceptModelSerializer(Serializer):
    token = UUIDField(required=True)
    email = EmailField(required=True)
    phone = CharField(required=True)
    password = CharField(required=True)
    profile = ProfileModelSerializer(required=True)

    def validate_phone(self, validated_data):
        digits = re.findall(r'\d', validated_data)
        if len(digits) < 9:
            raise ValidationError('Phone number must be at least 9 digits')
        phone = ''.join(digits)
        return phone.removeprefix('998')

    def validate(self, validated_data):
        token = validated_data['token']
        invitation = WorkspaceInvitation.objects.filter(token=token).first()
        if not invitation:
            raise ValidationError('taklif havolasi mavjud emas ! ')
        if invitation.expires_at <= timezone.now():
            raise ValidationError(" Tokenning muddati o'tgan ")
        if invitation.status != WorkspaceInvitation.Status.PENDING:
            raise ValidationError('Token yaroqsiz ')
        if invitation.email != validated_data['email']:
            raise ValidationError('Email mos kelmadi')

        return validated_data


class InvitationAcceptModelSerializer(Serializer):
    token = UUIDField(required=True)

    def validate(self, validated_data):
        token = validated_data['token']
        invitation = WorkspaceInvitation.objects.filter(token=token).first()
        if not invitation:
            raise ValidationError('taklif havolasi mavjud emas ! ')
        if invitation.expires_at <= timezone.now():
            raise ValidationError(" Tokenning muddati o'tgan ")
        if invitation.status != WorkspaceInvitation.Status.PENDING:
            raise ValidationError('Token yaroqsiz ')
        request = self.context['request']
        if invitation.email != request.user.email:
            raise ValidationError('Email mos kelmadi')

        return validated_data
