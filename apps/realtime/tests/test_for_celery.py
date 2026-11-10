from task.tasks import send_assignee_notification_task, send_status_notification_task

import pytest
from django.core import mail
from django.utils import timezone

from notification.models import Notification
from task.models import Task
from notification.tasks import mark_as_overdue   # task qaysi faylda bo'lsa, shuni yozing
from datetime import timedelta
from unittest.mock import patch
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



def make_overdue(task, status="TODO"):
    Task.objects.filter(pk=task.pk).update(
        deadline=timezone.now() - timedelta(hours=1), status=status
    )


@patch("notification.tasks.send_task_reminders")
def test_overdue_task_is_marked(mock_reminders, task):
    make_overdue(task)

    mark_as_overdue()

    task.refresh_from_db()
    assert task.is_overdue is True
    assert task.is_overdue is not None
    mock_reminders.delay.assert_called_once()
    args, kwargs = mock_reminders.delay.call_args

    assert args[0] == [task.id]
    assert kwargs["type"] == Notification.NotificationType.TASK_OVERDUE

@patch("notification.tasks.send_task_reminders")
def test_done_task_is_not_marked(mock_reminders, task):
    make_overdue(task, status="DONE")

    mark_as_overdue()

    task.refresh_from_db()
    assert task.is_overdue is False
    mock_reminders.delay.assert_not_called()


@patch("notification.tasks.send_task_reminders")
def test_task_without_deadline_is_not_marked(mock_reminders, task):
    # `task` fixture'ida deadline yo'q
    mark_as_overdue()

    task.refresh_from_db()
    assert task.is_overdue is False
    mock_reminders.delay.assert_not_called()


@patch("notification.tasks.send_task_reminders")
def test_future_deadline_is_not_marked(mock_reminders, ready_task):
    # `ready_task` deadline'i 3 kun keyin
    mark_as_overdue()

    ready_task.refresh_from_db()
    assert ready_task.is_overdue is False
    mock_reminders.delay.assert_not_called()


@patch("notification.tasks.send_task_reminders")
def test_second_run_does_not_notify_again(mock_reminders, task):
    make_overdue(task)

    mark_as_overdue()
    mark_as_overdue()

    mock_reminders.delay.assert_called_once()


def test_overdue_sends_notification_and_email(task):
    # mock yo'q: conftest'dagi celery_eager tufayli ikkinchi task ham shu yerda ishlaydi
    make_overdue(task)

    mark_as_overdue()

    assert len(mail.outbox) == 1
    assert mail.outbox[0].to == [task.assignee.user.email]
    assert Notification.objects.filter(
        recipient=task.assignee.user,
        notification_type=Notification.NotificationType.TASK_OVERDUE,
    ).exists()