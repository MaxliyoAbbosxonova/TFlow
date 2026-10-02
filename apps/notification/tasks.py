from datetime import date, timedelta

from celery import shared_task
from django.core.mail import send_mail

from notification.models import Notification
from services.notification import send_notification
from task.models import Task


@shared_task
def notify_upcoming_deadlines():
    tomorrow = date.today() + timedelta(days=1)

    tasks = Task.objects.filter(
        deadline__date=tomorrow,
        status__in=['TODO', 'IN_PROGRESS'],
    ).select_related('assignee')

    for task in tasks:
        if task.assignee and task.assignee.user.email:
            send_task_reminder.delay(task.id)

    return f"{tasks.count()} ta task uchun eslatma yuborildi"


@shared_task(bind=True, max_retries=3)
def send_task_reminder(self, task_id):
    try:
        task = Task.objects.select_related('assignee').get(id=task_id)
        subject="Deadline yaqinlashmoqda"
        message = f'"{task.title}" tasking deadline ertaga tugaydi.'
        send_notification(
            recipient=task.assignee.user,
            title=subject,
            message=message,
            notification_type=Notification.NotificationType.DEADLINE_SOON
        )

        send_mail(
            subject=subject,
            message=message,
            from_email="makhliyoabboskhonova@gmail.com",
            recipient_list=[task.assignee.user.email],
            fail_silently=False,
        )
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60)