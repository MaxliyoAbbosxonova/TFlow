from notification.models import Notification
from users.models import Profile, Users

"""Notification Modeli uchun testlar """


def test_delete_notification_when_recipient_deleted(db):
    profile = Profile.objects.create(
        username="Other", first_name="O", last_name="O",
        birth="2026-10-06T11:06:08.887Z", image="string", bio="string",
    )
    other = Users.objects.create_user(
        password="testpass123", email="other@example.com",
        phone="98888888", profile=profile,
    )
    n = Notification.objects.create(
        recipient=other,
        notification_type=Notification.NotificationType.MENTION,
        title="Hi",
        message="Hello",
    )
    pk = n.pk
    other.delete()
    assert not Notification.objects.filter(pk=pk).exists()


def test_delete_notification_when_comment_deleted(user, comment, notification):
    n = Notification.objects.create(
        recipient=user,
        notification_type=Notification.NotificationType.MENTION,
        title="Mention",
        message="Siz eslatildingiz",
        comment=comment,
    )
    pk = n.pk
    comment.delete()
    assert not Notification.objects.filter(pk=pk).exists()


def test_delete_notification_when_task_deleted(task, notification):
    pk = notification.id
    task.delete()
    assert not Notification.objects.filter(id=pk).exists()
