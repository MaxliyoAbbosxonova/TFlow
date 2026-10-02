import time

from celery import shared_task
from django.core.mail import send_mail

from notification.models import Notification
from root.settings import FRONTEND_URL
from services.notification import send_notification
from users.models import Users


@shared_task
def test_task():
    time.sleep(3)
    print("Celery task bajarildi!")
    return "OK"


@shared_task
def send_invitation_email_task(invitation_id):
    from workspace.models import WorkspaceInvitation

    invitation = WorkspaceInvitation.objects.select_related('workspace', 'invited_by__user').get(id=invitation_id)
    accept_url = f"{FRONTEND_URL}/invite/accept/{invitation.token}/"
    subject = f"{invitation.workspace.name} workspace'iga taklif"
    message = f"Sizni {invitation.workspace.name} workspace'iga taklif qilishdi.\nQabul qilish uchun: {accept_url}"
    user=Users.objects.filter(email=invitation.email).first()
    send_notification(recipient=user,
                      notification_type=Notification.NotificationType.WORKSPACE_INVITATION,
                      title=subject,
                      message=message,
                      )
    send_mail(
        subject=subject,
        message=message,
        from_email="makhliyoabboskhonova@gmail.com",
        recipient_list=[invitation.email],
        fail_silently=False,
    )


@shared_task
def send_invitation_accept_email_task(member):
    from workspace.models import Workspace

    workspace = Workspace.objects.filter(id=member.workspace.id).first()
    subject = 'your workspace invitation is accepted'
    message = f"Siz {workspace.name} workspace'iga qabul qilinganingiz bilan Tabriklaymiz.\nSizga berilgan ishchi roli {member.role}"
    send_notification(recipient=member.user,
                      notification_type=Notification.NotificationType.WORKSPACE_INVITATION,
                      title=subject,
                      message=message
                      )
    send_mail(
        subject=subject,
        message=message,
        from_email="makhliyoabboskhonova@gmail.com",
        recipient_list=[member.user.email],
        fail_silently=False,
    )
