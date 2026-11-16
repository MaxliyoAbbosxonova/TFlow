from django.core.exceptions import ValidationError
from django.db.models import (
    CASCADE,
    RESTRICT,
    SET_NULL,
    DateTimeField,
    ForeignKey,
    ManyToManyField,
    Model,
    TextChoices,
    TextField, IntegerField, PositiveSmallIntegerField, BooleanField, OneToOneField, PROTECT,
)
from django.db.models.constraints import UniqueConstraint
from django.db.models.fields import CharField
from mptt.fields import TreeForeignKey
from mptt.models import MPTTModel
from project.models import Project
from shared.models import FileUpload
from workspace.models import Workspace, WorkspaceMember

# Create your models here.


class Label(Model):
    name = CharField(max_length=100)
    color = CharField(max_length=7, default="#000000")
    workspace = ForeignKey(Workspace, on_delete=CASCADE)

    def __str__(self):
        return self.name



# Create your models here.
class Workflow(Model):
    project = OneToOneField(Project, on_delete=CASCADE, related_name="workflow")
    name = CharField(max_length=100)


class WorkflowStatus(Model):
    class Category (TextChoices):
        TODO = "TODO"
        IN_PROGRESS = "IN_PROGRESS"
        CODE_REVIEW = "CODE_REVIEW"
        QA="QA"
        DONE = "DONE"
        ARCHIVED = "ARCHIVED"

    workflow = ForeignKey(Workflow, on_delete=CASCADE, related_name="statuses")
    name = CharField(max_length=50)
    category = CharField(max_length=20, choices=Category.choices)
    order = PositiveSmallIntegerField(default=0)
    is_initial = BooleanField(default=False)   # yengi vazifa shu statusda boshlanadi True demak eng birinchi status

    class Meta:
        constraints =  [UniqueConstraint(fields=["workflow", "name"], name="uniq_status_name")]

class WorkflowTransition (Model):
    workflow = ForeignKey(Workflow, on_delete=CASCADE, related_name="transitions")
    from_status = ForeignKey(WorkflowStatus, on_delete=CASCADE, related_name="+")
    to_status = ForeignKey(WorkflowStatus, on_delete=CASCADE, related_name="+")

    class Meta:
        constraints =  [UniqueConstraint(fields=["from_status", "to_status"], name="uniq_transition")]


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
    title = CharField(max_length=255, default='improvement')
    description = TextField(max_length=500, default='Improve bugs')
    assignee = ForeignKey(WorkspaceMember, related_name='assigned_task', null=True, on_delete=RESTRICT, blank=True)
    reporter = ForeignKey(WorkspaceMember, related_name='reported_task', on_delete=RESTRICT, null=True)
    priority = CharField(max_length=10, choices=Priority.choices, default=Priority.LOW)
    deadline = DateTimeField(null=True, blank=True)
    status = ForeignKey("WorkflowStatus", on_delete=PROTECT, related_name="tasks")
    file = ForeignKey(FileUpload, on_delete=SET_NULL, null=True, blank=True)
    project = ForeignKey(Project, on_delete=CASCADE, null=True, related_name='tasks')
    label = ManyToManyField(Label, related_name="tasks")
    created_at = DateTimeField(auto_now_add=True, )
    completed_at = DateTimeField(null=True, blank=True)
    is_overdue = BooleanField(default=False)

    class MPTTMeta:
        order_insertion_by = ['title']

    def clean(self):
        super().clean()
        if self.parent_id and self.parent.project_id != self.project_id:
            raise ValidationError(
                {"parent": "Subtask parent taskning projectidan tashqarida bo'lishi mumkin emas."})

    def save(self, *args, **kwargs):
        self.full_clean()  # admin/serializerdan tashqarida ham tekshirilishi uchun
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title
