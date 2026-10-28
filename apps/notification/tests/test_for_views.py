from django.urls import reverse
from notification.models import Notification

"""Notification viewlari uchun testlar"""


def test_list_returns_only_own_notifications(auth_client, notification, stranger):
    """Ro'yxatda faqat o'z notification'lari bo'ladi."""
    Notification.objects.create(
        recipient=stranger,
        notification_type=Notification.NotificationType.MENTION,
        title="Begona", message="x",
    )
    r = auth_client.get(reverse("notifications-list"))
    assert r.status_code == 200, r.data
    ids = [n["id"] for n in r.data["results"]]
    assert ids == [notification.id]


def test_list_anonymous_is_rejected(api_client, db):
    """Login qilmagan foydalanuvchi ro'yxatni ko'ra olmaydi."""
    r = api_client.get(reverse("notifications-list"))
    assert r.status_code in (401, 403)


def test_cannot_read_other_users_notification(api_client, stranger, notification):
    """Boshqa odamning notification'i ochilmaydi va o'qilgan bo'lib qolmaydi."""
    api_client.force_authenticate(user=stranger)
    r = api_client.get(reverse("notifications-read", args=[notification.id]))
    assert r.status_code == 404
    notification.refresh_from_db()
    assert notification.is_read is False


def test_owner_read_marks_notification_as_read(auth_client, notification):
    """Egasi ochganda notification o'qilgan bo'ladi."""
    r = auth_client.get(reverse("notifications-read", args=[notification.id]))
    assert r.status_code == 200, r.data
    notification.refresh_from_db()
    assert notification.is_read is True
