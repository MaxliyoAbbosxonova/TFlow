from django.contrib.contenttypes.models import ContentType

from audit_log.models import AuditLog


def create_audit_log(actor, action, model, old_value=None, new_value=None):
    AuditLog.objects.create(
        actor=actor,
        action=action,
        content_type=ContentType.objects.get_for_model(model),
        object_id=model.id,
        old_value=old_value,
        new_value=new_value
    )
