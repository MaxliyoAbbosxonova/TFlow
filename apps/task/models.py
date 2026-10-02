from django.core.exceptions import ValidationError
from django.db.models import DateTimeField, Model
from django.db.models import ManyToManyField, CASCADE, TextChoices, \
    TextField, ForeignKey, RESTRICT
from django.db.models.fields import CharField
from mptt.fields import TreeForeignKey
from mptt.models import MPTTModel

from project.models import Project
from shared.models import FileUpload
from workspace.models import WorkspaceMember, Workspace


# Create your models here.



class Label(Model):
    name = CharField(max_length=100)
    color=CharField(max_length=7, default="#000000")
    workspace=ForeignKey(Workspace,on_delete=CASCADE)

    def __str__(self):
        return self.name



class Task(MPTTModel):
    class Workflow(TextChoices):
        TODO = 'TODO', 'todo'
        IN_PROGRESS = 'IN_PROGRESS', 'in_progres'
        CODE_REVIEW = 'CODE_REVIEW', 'code_review'
        QA = 'QA', 'qa'
        DONE = 'DONE', 'done'
        ARCHIVED = 'ARCHIVED', 'archived'

    class Priority(TextChoices):
        LOW = 'LOW', 'low'
        MEDIUM = 'MEDIUM', 'medium'
        HIGH = 'HIGH', 'high'
        CRITICAL = 'CRITICAL', 'critical'

    parent = TreeForeignKey('self', CASCADE, null=True, blank=True)
    title = CharField(max_length=32, default='improvement')
    description = TextField(max_length=500, default='Improve bugs')
    assignee = ForeignKey(WorkspaceMember, related_name='assigned_task', null=True, on_delete=RESTRICT)
    reporter = ForeignKey(WorkspaceMember, related_name='reported_task', on_delete=RESTRICT, null=True)
    priority = CharField(max_length=10, choices=Priority.choices, default=Priority.LOW)
    deadline = DateTimeField(null=True, blank=True)
    status = CharField(max_length=15, choices=Workflow.choices, default=Workflow.TODO)
    file = ForeignKey(FileUpload, on_delete=CASCADE, null=True, blank=True)
    project = ForeignKey(Project, on_delete=CASCADE, null=True, related_name='tasks')
    label = ManyToManyField(Label, related_name="tasks")
    created_at=DateTimeField(auto_now_add=True,)
    completed_at =DateTimeField(null=True, blank=True)

    class MPTTMeta:
        order_insertion_by = ['title']

    def clean(self):
        super().clean()
        if self.parent.id and self.parent.project_id != self.project_id:
            raise ValidationError(
                {"parent": "Subtask parent taskning projectidan tashqarida bo'lishi mumkin emas."}
            )

    def save(self, *args, **kwargs):
        self.full_clean()  # admin/serializerdan tashqarida ham tekshirilishi uchun
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

