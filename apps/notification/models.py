from comment.models import Comments
from django.db.models import (
    CASCADE,
    BooleanField,
    DateTimeField,
    ForeignKey,
    Model,
    TextChoices,
    TextField,
)
from django.db.models.fields import CharField
from task.models import Task
from users.models import Users

# Create your models here.


class Notification(Model):
    class NotificationType(TextChoices):
        TASK_ASSIGNED = "TASK_ASSIGNED", "Task assigned"
        MENTION = "MENTION", "Mention"
        STATUS_CHANGED = "STATUS_CHANGED", "Status changed"
        DEADLINE_SOON = "DEADLINE_SOON", "Deadline soon"
        TASK_OVERDUE = "TASK_OVERDUE", "Task overdue"
        WORKSPACE_INVITATION = 'WORKSPACE_INVITATION', 'workspace_invitation'

    recipient = ForeignKey(Users, on_delete=CASCADE, related_name="notifications")
    notification_type = CharField(max_length=50, choices=NotificationType.choices)
    title = CharField(max_length=255)
    message = TextField()
    task = ForeignKey(Task, on_delete=CASCADE, null=True, blank=True, related_name="notifications")
    comment = ForeignKey(Comments, on_delete=CASCADE, null=True, blank=True, related_name="notifications")
    is_read = BooleanField(default=False)
    created_at = DateTimeField(auto_now_add=True)
    read_at = DateTimeField(null=True, blank=True)
