from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from workspace.models import WorkspaceInvitation
from workspace.tasks import send_invitation_email_task


@transaction.atomic
def create_invitation(validated_data):
    data = validated_data.copy() # data ni to'g'ridan to'g'ri o'zgartirmaslik uchun
    email = data['email']
    inviter = data['invited_by']
    role = data['role']
    workspace = data['workspace']

    invitation = WorkspaceInvitation.objects.create(
        workspace=workspace,
        email=email,
        role=role,
        invited_by=inviter,
        expires_at=timezone.now() + timedelta(days=7)
    )
    send_invitation_email_task.delay(invitation.id)
    transaction.on_commit(lambda: send_invitation_email_task.delay(invitation.id))

    return invitation
