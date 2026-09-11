from django.db.models import DateTimeField
from django.db.models import Model, CASCADE, TextChoices, \
    TextField, ForeignKey, RESTRICT
from django.db.models.fields import CharField

from team.models import Team
from workspace.models import Workspace, WorkspaceMember


# Create your models here.

class Project(Model):
    class Status(TextChoices):
        PLANNED = 'PLANNED', 'planned'
        ACTIVE = 'ACTIVE', 'active'
        COMPLETED = 'COMPLETED', 'completed'
        ARCHIVED = 'ARCHIVED', 'archived'

    title = CharField(max_length=100, unique=True, default="Name")
    team = ForeignKey(Team, related_name='projects', on_delete=RESTRICT, null=True,blank=True)
    workspace = ForeignKey('workspace.Workspace', related_name="products", null=True, on_delete=CASCADE)
    member = ForeignKey(WorkspaceMember, related_name='project', on_delete=RESTRICT, null=True)
    status = CharField(max_length=15, choices=Status.choices, default=Status.PLANNED)
    description = TextField(max_length=320, null=True)
    start_date = DateTimeField(auto_now_add=True)
    deadline = DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.title
