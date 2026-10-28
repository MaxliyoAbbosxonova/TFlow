from django.core import mail
from notification.models import Notification
from task.tasks import send_assignee_notification_task, send_status_notification_task


def test_assignee_task_sends_email(task):
    """Assignee task'i assignee'ga email yuboradi."""
    send_assignee_notification_task.delay(task.id)
    assert len(mail.outbox) == 1
    assert mail.outbox[0].to == [task.assignee.user.email]


def test_assignee_task_creates_assigned_notification(task):
    """Assignee task'i TASK_ASSIGNED turidagi notification yozadi."""
    send_assignee_notification_task.delay(task.id)
    n = Notification.objects.get(recipient=task.assignee.user)
    assert n.notification_type == Notification.NotificationType.TASK_ASSIGNED


def test_status_task_uses_status_changed_type(task):
    """Status task'i STATUS_CHANGED turidagi notification yozadi."""
    send_status_notification_task.delay(task.id)
    n = Notification.objects.get(recipient=task.assignee.user)
    assert n.notification_type == Notification.NotificationType.STATUS_CHANGED


def test_status_task_message_contains_status(task):
    """Xabarda joriy status ko'rsatiladi."""
    send_status_notification_task.delay(task.id)
    assert task.status in mail.outbox[0].body