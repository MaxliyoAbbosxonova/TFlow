import uuid

from django.db.models import ImageField
from django.db.models import Model, ManyToManyField, CASCADE, TextChoices, \
    TextField, ForeignKey, RESTRICT
from django.db.models.fields import CharField, EmailField, DateTimeField, UUIDField
from django.utils import timezone

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


class WorkspaceMember(Model):
    class Role(TextChoices):
        ADMIN = "ADMIN", 'admin'
        WORKSPACE_OWNER = "WORKSPACE_OWNER", 'workspace_owner'
        MANAGER = "MANAGER", 'manager'
        TEAM_LEAD = "TEAM_LEAD", 'team_lead'
        EMPLOYEE = "EMPLOYEE", 'employee'

    workspace = ForeignKey(Workspace, related_name='members', on_delete=CASCADE, null=True, blank=True)
    team = ManyToManyField('team.Team', related_name='members')
    user = ForeignKey(Users, related_name='members', on_delete=CASCADE)
    role = CharField(max_length=15, choices=Role.choices, default=Role.EMPLOYEE)

    def __str__(self):
        return self.role


class WorkspaceInvitation(Model):
    class Status(TextChoices):
        PENDING = 'PENDING', 'pending'
        ACCEPTED = 'ACCEPTED', 'accepted'
        EXPIRED = 'EXPIRED', 'expired'
        REVOKED = 'REVOKED', 'revoked'

    workspace = ForeignKey('workspace.Workspace', on_delete=CASCADE, related_name='invitations')
    email = EmailField()
    invited_by = ForeignKey('workspace.WorkspaceMember', on_delete=CASCADE, related_name='sent_invitations')
    role = CharField(max_length=15, choices=WorkspaceMember.Role.choices, default=WorkspaceMember.Role.EMPLOYEE)
    token = UUIDField(default=uuid.uuid4, unique=True, editable=False)
    status = CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    created_at = DateTimeField(auto_now_add=True)
    expires_at = DateTimeField()

    def is_valid(self):
        return self.status == self.Status.PENDING and self.expires_at > timezone.now()
