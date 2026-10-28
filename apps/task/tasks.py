from celery import shared_task
from comment.models import Comments
from django.core.mail import send_mail
from notification.models import Notification
from services.notification import send_notification
from task.models import Task
from users.models import Profile


@shared_task
def send_assignee_notification_task(task_id):
    from workspace.models import Workspace
    task=Task.objects.filter(id=task_id).first()
    workspace = Workspace.objects.filter(id=task.project.workspace.id).first()
    subject = f'Task Assigned'
    message = f"Siz {workspace.name} workspace'dagi {task.project.title} ga assignee qilindingiz.\n"
    send_notification(recipient=task.assignee.user,
                      notification_type=Notification.NotificationType.TASK_ASSIGNED,
                      title=subject,
                      message=message
                      )
    send_mail(
        subject=subject,
        message=message,
        from_email="makhliyoabboskhonova@gmail.com",
        recipient_list=[task.assignee.user.email],
        fail_silently=False,
    )


@shared_task
def send_status_notification_task(task_id):
    from workspace.models import Workspace
    task = Task.objects.filter(id=task_id).first()
    workspace = Workspace.objects.filter(id=task.project.workspace.id).first()
    subject = f'Task Status Changed'
    message = (
        f"Siz assignee qilingan {workspace.name} workspace'dagi {task.project.title} projectga tegishli  Task statusi o'zgartirildi.\n"
        f"Status {task.status}")
    send_notification(recipient=task.assignee.user,
                      notification_type=Notification.NotificationType.STATUS_CHANGED,
                      title=subject,
                      message=message
                      )
    send_mail(
        subject=subject,
        message=message,
        from_email="makhliyoabboskhonova@gmail.com",
        recipient_list=[task.assignee.user.email],
        fail_silently=False,
    )


@shared_task
def comment_mention_email_task(profile_id, comment_id, task_id, text):
    comment=Comments.objects.filter(id=comment_id).first()
    task = Task.objects.filter(id=task_id).first()
    profile=Profile.objects.filter(id=profile_id).first()
    subject = f"@{comment.author.profile.username} Mentioned you on comment"
    send_notification(recipient=profile.user,
                      notification_type=Notification.NotificationType.MENTION,
                      comment=comment,
                      task=task,
                      message=text,
                      title=f"@{comment.author.profile.username} Mentioned you on comment"
                      )
    send_mail(
        subject=subject,
        message=text,
        from_email="makhliyoabboskhonova@gmail.com",
        recipient_list=[profile.user.email],
        fail_silently=False,
    )
