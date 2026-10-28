from datetime import date, timedelta

from celery import shared_task
from django.core.mail import send_mail

from notification.models import Notification
from services.notification import send_notification
from task.models import Task


# optimisation
@shared_task
def notify_upcoming_deadlines():
    tomorrow = date.today() + timedelta(days=1)
    task_ids = list(Task.objects.filter(deadline__date=tomorrow, status__in=['TODO', 'IN_PROGRESS'],
                                        assignee__isnull=False, assignee__user__email__gt='').values_list('id',
                                                                                                          flat=True))
    if task_ids:
        send_task_reminders.delay(task_ids)

    return f"{len(task_ids)} ta task uchun eslatma yuborildi"



@shared_task(bind=True, max_retries=3)
def send_task_reminders(self, task_ids):
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

            subject = "Deadline yaqinlashmoqda"
            message = f'"{task.title}" taskining deadline muddati ertaga tugaydi.'

            send_notification(
                recipient=user,
                title=subject,
                message=message,
                notification_type=Notification.NotificationType.DEADLINE_SOON,
            )

            send_mail(
                subject=subject,
                message=message,
                from_email="makhliyoabboskhonova@gmail.com",
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
