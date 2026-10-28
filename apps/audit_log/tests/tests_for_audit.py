import pytest
from audit_log.models import AuditLog
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse
from services.audit import create_audit_log

"""Audit_log yaratilgan barcha joydagi funksiya turlari uchun testlar"""

def test_creates_log_with_values(task, member):
    """Funksiya action, eski va yangi qiymat bilan yozuv yaratadi."""
    create_audit_log(member, "CHANGED PRIORITY", task,
                     old_value={"priority": "LOW"}, new_value={"priority": "HIGH"})
    log = AuditLog.objects.get(object_id=task.id)
    assert log.action == "CHANGED PRIORITY"
    assert log.old_value == {"priority": "LOW"}
    assert log.new_value == {"priority": "HIGH"}
    assert log.actor == member


def test_log_points_to_correct_object(task, member):
    """GenericForeignKey aynan shu task'ga ulanadi."""
    create_audit_log(member, "CREATE", task)
    log = AuditLog.objects.get(object_id=task.id)
    assert log.content_type == ContentType.objects.get_for_model(task)
    assert log.content_object == task


def test_works_for_different_models(task, label, member):
    """Turli model (Task, Label) uchun content_type farq qiladi."""
    create_audit_log(member, "A", task)
    create_audit_log(member, "B", label)
    types = set(AuditLog.objects.values_list("content_type", flat=True))
    assert len(types) == 2


def test_actor_can_be_none(task):
    """actor bo'lmasa ham yozuv yaratiladi."""
    create_audit_log(None, "SYSTEM", task)
    assert AuditLog.objects.get(object_id=task.id).actor is None


def test_old_and_new_values_default_to_none(task, member):
    """Qiymatlar berilmasa None saqlanadi."""
    create_audit_log(member, "X", task)
    log = AuditLog.objects.get(object_id=task.id)
    assert log.old_value is None and log.new_value is None


def test_none_model_raises(member):
    """model None bo'lsa AttributeError (kod himoyasiz)."""
    with pytest.raises(AttributeError):
        create_audit_log(member, "X", None)


def test_change_priority_logs_actor_who_changed(api_client, task, member, manager):
    """Audit logda priority'ni o'zgartirgan odam yoziladi, task muallifi emas."""
    manager_user, manager_member = manager

    # tayyorlash: o'zgartiruvchi task muallifidan farq qilishi shart
    assert task.reporter_id != manager_member.id

    # harakat: manager API orqali priority o'zgartiradi
    api_client.force_authenticate(user=manager_user)
    r = api_client.patch(
        reverse("change-priority", args=[task.id]), {"priority": "HIGH"}
    )
    assert r.status_code == 200, r.data

    # tekshirish
    log = AuditLog.objects.get(object_id=task.id, action="CHANGED PRIORITY")
    assert log.actor_id == manager_member.id


from datetime import timedelta

from django.utils import timezone


def test_change_deadline_logs_actor_who_changed(api_client, task, manager):
    """Audit logda deadline'ni o'zgartirgan odam yoziladi."""
    manager_user, manager_member = manager
    assert task.reporter_id != manager_member.id
    api_client.force_authenticate(user=manager_user)
    new = (timezone.now() + timedelta(days=5)).isoformat()
    r = api_client.patch(reverse("change-deadline", args=[task.id]), {"deadline": new})
    assert r.status_code == 200, r.data
    log = AuditLog.objects.get(object_id=task.id, action="CHANGED DEADLINE")
    assert log.actor_id == manager_member.id


def test_change_assignee_logs_actor_who_changed(api_client, task, manager, team_member):
    """Audit logda assignee'ni o'zgartirgan odam yoziladi."""
    manager_user, manager_member = manager
    _, new_assignee = team_member
    api_client.force_authenticate(user=manager_user)
    r = api_client.patch(reverse("change-assignee", args=[task.id, new_assignee.id]), {})
    assert r.status_code == 200, r.data
    log = AuditLog.objects.get(object_id=task.id, action="CHANGED ASSIGNEE")
    assert log.actor_id == manager_member.id


def test_change_status_logs_actor_from_same_workspace(api_client, ready_task, manager):
    """Status logida actor shu task workspace'idagi a'zolik bo'ladi."""
    manager_user, manager_member = manager
    api_client.force_authenticate(user=manager_user)
    r = api_client.patch(reverse("task-change-status", args=[ready_task.id]),
                         {"status": "IN_PROGRESS"})
    assert r.status_code == 200, r.data
    log = AuditLog.objects.get(object_id=ready_task.id, action="CHANGED STATUS")
    assert log.actor_id == manager_member.id
