from django.db.models import ImageField, DateTimeField, FileField
from django.db.models import Model, OneToOneField, ManyToManyField, CASCADE, TextChoices, \
    TextField, ForeignKey, RESTRICT
from django.db.models.fields import CharField
from mptt.fields import TreeForeignKey
from mptt.models import MPTTModel

from users.models import Users


# Create your models here.

class Workspace(Model):
    name = CharField(max_length=200, unique=True)
    description = TextField(max_length=320, null=True)
    logo = ImageField(upload_to="w_logos/",
                      null=True,
                      blank=True)
    owner = ForeignKey(Users, on_delete=RESTRICT, null=True)

    def __str__(self):
        return self.name


class Team(Model):
    name = CharField(max_length=100, unique=True)
    workspace = ForeignKey(Workspace, related_name='team', on_delete=CASCADE, default=1)
    team_lead = ForeignKey(Users, on_delete=RESTRICT, null=True)

    def __str__(self):
        return self.name


class WorkspaceMember(Model):
    class Role(TextChoices):
        ADMIN = "ADMIN", 'admin'
        WORKSPACE_OWNER = "WORKSPACE_OWNER", 'workspace_owner'
        MANAGER = "MANAGER", 'manager'
        TEAM_LEAD = "TEAM_LEAD", 'team_lead'
        EMPLOYEE = "EMPLOYEE", 'employee'

    workspace = ManyToManyField(Workspace, related_name='members')
    team = ManyToManyField(Team, related_name='members')
    user = OneToOneField(Users, related_name='members', on_delete=CASCADE)
    role = CharField(max_length=15, choices=Role.choices, default=Role.EMPLOYEE)

    def __str__(self):
        return self.role


class Project(Model):
    class Status(TextChoices):
        PLANNED = 'PLANNED', 'planned'
        ACTIVE = 'ACTIVE', 'active'
        COMPLETED = 'COMPLETED', 'completed'
        ARCHIVED = 'ARCHIVED', 'archived'

    class Workflow(TextChoices):
        TODO = 'TODO ', 'todo'
        IN_PROGRESS = 'IN_PROGRESS', 'in_progres'
        CODE_REVIEW = 'CODE_REVIEW', 'code_review'
        QA = 'QA ', 'qa'
        DONE = 'DONE ', 'done'

    title = CharField(max_length=100, unique=True, default="Name")
    team = ForeignKey(Team, related_name='project', on_delete=RESTRICT, null=True)
    workspace = ForeignKey(Workspace, related_name="products", null=True, on_delete=CASCADE)
    member = ForeignKey(WorkspaceMember, related_name='project', on_delete=RESTRICT, null=True)
    status = CharField(max_length=15, choices=Status.choices, default=Status.PLANNED)
    description = TextField(max_length=320, null=True)
    start_date = DateTimeField(auto_now_add=True)
    deadline = DateTimeField(null=True, blank=True)
    workflow = CharField(max_length=16, choices=Workflow.choices, default=Workflow.TODO)

    def __str__(self):
        return self.title


class Task(MPTTModel):
    class Status(TextChoices):
        CREATED = 'CREATED', 'created'
        ASSIGNED = 'ASSIGNED', 'assigned'
        COMPLETED = 'COMPLETED', 'completed'
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
    status = CharField(max_length=15, choices=Status.choices, default=Status.CREATED)
    file = FileField(upload_to="tasks/", null=True, blank=True)
    project = ForeignKey(Project, on_delete=CASCADE, null=True)

    class MPTTMeta:
        order_insertion_by = ['title']

    def __str__(self):
        return self.title
