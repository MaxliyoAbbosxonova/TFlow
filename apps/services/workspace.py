from django.db import transaction

from users.models import Users, Profile
from workspace.models import WorkspaceInvitation, WorkspaceMember


@transaction.atomic
def Invitation_Anonymouse_Accept(validated_data):
    email = validated_data['email']
    phone = validated_data['phone']
    token = validated_data.pop('token')
    invitation = WorkspaceInvitation.objects.filter(token=token).first()
    user = Users.objects.filter(email=email, phone=phone).first()
    if not user:
        password = validated_data.pop('password')
        item = validated_data.pop('profile')
        user = Users(**validated_data, profile=Profile.objects.create(**item))
        user.set_password(password)
        user.save()

    member, _ = WorkspaceMember.objects.get_or_create(workspace=invitation.workspace, user=user,
                                                      defaults={'role': invitation.role})
    invitation.status = 'ACCEPTED'
    invitation.save(update_fields=['status'])
    return member


@transaction.atomic
def Invitation_Accept(validated_data):
    token = validated_data.pop('token')
    invitation = WorkspaceInvitation.objects.filter(token=token).first()
    user = Users.objects.filter(email=invitation.email).first()
    member, _ = WorkspaceMember.objects.get_or_create(workspace=invitation.workspace, user=user,
                                                      defaults={'role': invitation.role})
    invitation.status = 'ACCEPTED'
    invitation.save(update_fields=['status'])
    return member
