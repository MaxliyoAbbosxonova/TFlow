import os
from datetime import date, timedelta

from celery import shared_task
from django.core.mail import send_mail
from django.utils import timezone

from notification.models import Notification
from services.notification import send_notification
from task.models import Task

from_email= os.getenv('EMAIL_HOST_USER')

# optimisation
@shared_task
def notify_upcoming_deadlines():
    tomorrow = date.today() + timedelta(days=1)
    task_ids = list(Task.objects.filter(deadline__date=tomorrow, status__in=['TODO', 'IN_PROGRESS'],
                                        assignee__isnull=False, assignee__user__email__gt='').values_list('id',
                                                                                                          flat=True))
    subject = "Deadline yaqinlashmoqda"
    message = f' taskining deadline muddati ertaga tugaydi.'
    type=Notification.NotificationType.TASK_OVERDUE

    if task_ids:
        send_task_reminders.delay(task_ids,subject=subject,message=message,type=type)

    return f"{len(task_ids)} ta task uchun eslatma yuborildi"


@shared_task
def mark_as_overdue():
    now=timezone.now()
    task_ids=list(Task.objects.filter(deadline__lt=now,is_overdue=False,status__in=['IN_PROGRESS','TODO']).values_list('id',flat=True))
    subject = "Deadline tugadi"
    message = f' taskining deadline muddati tugadi .'
    type=Notification.NotificationType.TASK_OVERDUE
    if not task_ids:
        return "overdue task yo'q"

    Task.objects.filter(id__in=task_ids).update(is_overdue=True)
    send_task_reminders.delay(task_ids, subject=subject, message=message,type=type)
    return f"{len(task_ids)} ta task overdue deb belgilandi"

@shared_task(bind=True, max_retries=3)
def send_task_reminders(self, task_ids,subject,message,type):
    tasks = Task.objects.filter(
        id__in=task_ids,
        assignee__isnull=False,
    ).select_related(
        'assignee__user'
    )

    failed_ids = []

    for task in tasks:
        try:
            user = task.assignee.user

            if not user.email:
                continue



            send_notification(
                recipient=user,
                title=subject,
                message=f'"{task.title}"'+message,
                notification_type=type,
            )

            send_mail(
                subject=subject,
                message=f'"{task.title}"'+message,
                from_email=from_email,
                recipient_list=[user.email],
                fail_silently=False,
            )

        except Exception:
            failed_ids.append(task.id)

    if failed_ids:
        raise self.retry(
            args=[failed_ids],
            countdown=60,
        )

    return f"{len(task_ids)} ta task qayta ishlandi"

