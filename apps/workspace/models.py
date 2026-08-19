from django.db.models import ImageField, DateTimeField
from django.db.models import Model, OneToOneField, ManyToManyField, CASCADE, TextChoices, \
    TextField, ForeignKey, RESTRICT
from django.db.models.fields import CharField
from django.utils import timezone
from mptt.fields import TreeForeignKey
from mptt.models import MPTTModel

from users.models import Users


# Create your models here.

class Workspace(Model):
    name = CharField(max_length=200)
    description = TextField(max_length=320, null=True)
    logo = ImageField(upload_to="w_logos/",
                      null=True,
                      blank=True)


class Team(Model):
    name = CharField(max_length=100)
    workspace = ManyToManyField(Workspace, related_name='team')


class WorkspaceMember(Model):
    class Role(TextChoices):
        ADMIN = "ADMIN", 'admin'
        WORKSPACE_OWNER = "WORKSPACE_OWNER", 'workspace_owner'
        MANAGER = "MANAGER", 'manager'
        TEAM_LEAD = "TEAM_LEAD", 'team_lead'
        EMPLOYEE = "EMPLOYEE", 'employee'

    workspace = ManyToManyField(Workspace, related_name='member',null=True)
    team = ManyToManyField(Team, related_name='member',null=True)
    user = OneToOneField(Users, related_name='member', on_delete=CASCADE)
    role = CharField(max_length=15, choices=Role.choices, default=Role.EMPLOYEE)


class Project(Model):
    class Status(TextChoices):
        PLANNED='PLANNED','planned'
        ACTIVE='ACTIVE','active'
        COMPLETED='COMPLETED','completed'
        ARCHIVED='ARCHIVED','archived'
    team = ForeignKey(Team, related_name='project', on_delete=RESTRICT, null=True)
    member = ForeignKey(WorkspaceMember,related_name='project',on_delete= RESTRICT,null=True)
    status=CharField(max_length=15,choices=Status.choices,default=Status.PLANNED)
    description=TextField(max_length=320,null=True)
    start_date=DateTimeField(auto_now_add=True)
    deadline=DateTimeField(auto_now=True)


class Task(Model,MPTTModel):
    class Status(TextChoices):
        CREATED='CREATED','created'
        ASSIGNED='ASSIGNED','assigned'
        COMPLETED='COMPLETED','completed'
        ARCHIVED='ARCHIVED','archived'
    class Priority(TextChoices):
        LOW='LOW','low'
        MEDIUM='MEDIUM','medium'
        HIGH='HIGH','high'
        CRITICAL='CRITICAL','critical'

    parent=TreeForeignKey('self',CASCADE,null=True,blank=True)
    title=CharField(max_length=32,default='improvement')
    description=TextField(max_length=500,default='Improve bugs')
    assignee=OneToOneField(WorkspaceMember,related_name='task',null=True, on_delete=RESTRICT)
    reporter=OneToOneField(WorkspaceMember,related_name='task',on_delete=RESTRICT,null=True)
    priority=CharField(max_length=10,choices=Priority.choices,default=Priority.LOW)
    deadline=DateTimeField(default=timezone.now())
    status=CharField(max_length=15,choices=Status.choices,default=Status.PLANNED)


class Subtask(Model):
    class Status(TextChoices):
        CREATED='CREATED','created'
        ASSIGNED='ASSIGNED','assigned'
        COMPLETED='COMPLETED','completed'
        ARCHIVED='ARCHIVED','archived'

    task=ForeignKey(Task,related_name='subtask',on_delete=CASCADE)
    description=TextField(default='improve bugs')
    assignee = OneToOneField(WorkspaceMember, related_name='task', null=True, on_delete=RESTRICT)
    reporter = OneToOneField(WorkspaceMember, related_name='task', on_delete=RESTRICT, null=True)
    status=CharField(max_length=15,choices=Status.choices,default=Status.PLANNED)
    deadline = DateTimeField(default=timezone.now())
