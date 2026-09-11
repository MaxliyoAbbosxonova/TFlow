from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db.models import DateTimeField, SET_NULL, PositiveBigIntegerField, JSONField
from django.db.models import Model, CASCADE, ForeignKey
from django.db.models.fields import CharField

from workspace.models import WorkspaceMember


# Create your models here.

class AuditLog(Model):
    actor = ForeignKey(
        WorkspaceMember,
        on_delete=SET_NULL,
        null=True,
        related_name="audit_logs"
    )

    action = CharField(max_length=100)

    content_type = ForeignKey(ContentType, on_delete=CASCADE)
    object_id = PositiveBigIntegerField()
    content_object = GenericForeignKey("content_type", "object_id")

    old_value = JSONField(null=True, blank=True)
    new_value = JSONField(null=True, blank=True)

    created_at = DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.content_type}'
