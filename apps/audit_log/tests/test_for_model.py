from audit_log.models import AuditLog
from django.contrib.contenttypes.models import ContentType

# Audit_Log modeli uchun testlar :


def test_str_returns_content_type(audit_log, workspace):
    expected = str(ContentType.objects.get_for_model(workspace))
    assert str(audit_log) == expected


def test_content_object_returns_related_object(audit_log, workspace):
    assert audit_log.content_object == workspace


def test_actor_set_null_when_member_deleted(audit_log, member):
    member.delete()
    audit_log.refresh_from_db()
    assert audit_log.actor is None


def test_log_survive_when_actor_deleted(audit_log, member):
    member.delete()
    assert AuditLog.objects.filter(id=audit_log.id).exists()


def test_created_at_is_set_automatically(audit_log):
    assert audit_log.created_at is not None
