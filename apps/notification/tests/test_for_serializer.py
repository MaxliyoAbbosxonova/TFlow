from types import SimpleNamespace

import pytest
from notification.serializers import NotificationRetrieveModelSerializer
from rest_framework.exceptions import NotFound

"""Notification uchun serializerlarga testlar """


def run_save(pk, user):
    s = NotificationRetrieveModelSerializer(
        context={"id": pk, "request": SimpleNamespace(user=user)}
    )
    return s.save()


def test_save_marks_notification_as_read(notification, user):
    """Notification ochilganda is_read True bo'ladi."""
    run_save(notification.id, user)
    notification.refresh_from_db()
    assert notification.is_read is True


def test_save_returns_notification_when_no_comment(notification, user):
    """Comment bog'lanmagan bo'lsa, notification o'zi qaytariladi."""
    result = run_save(notification.id, user)
    assert result == notification


def test_save_returns_comment_when_linked(notification, user, comment):
    """Comment bog'langan bo'lsa, comment qaytariladi."""
    notification.comment = comment
    notification.save()
    result = run_save(notification.id, user)
    assert result == comment


def test_save_unknown_notification_raises_not_found(db, user):
    """Mavjud bo'lmagan notification uchun NotFound ko'tariladi."""
    with pytest.raises(NotFound):
        run_save(999999, user)


def test_save_does_not_change_already_read_notification(notification, user):
    """Allaqachon o'qilgan notification o'zgarishsiz qoladi."""
    notification.is_read = True
    notification.save()
    run_save(notification.id, user)
    notification.refresh_from_db()
    assert notification.is_read is True
