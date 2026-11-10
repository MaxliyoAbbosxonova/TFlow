from django.db.models import CASCADE, DateTimeField, ForeignKey, TextField,DateField
from mptt.fields import TreeForeignKey
from mptt.models import MPTTModel

from task.models import Task
from users.models import Users

# Create your models here.


class Comments(MPTTModel):
    parent = TreeForeignKey('self', CASCADE, null=True, blank=True)
    author = ForeignKey(Users, on_delete=CASCADE, related_name='comments')
    task = ForeignKey(Task, on_delete=CASCADE, related_name="comments")
    text = TextField(max_length=512)
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateField(auto_now=True)
