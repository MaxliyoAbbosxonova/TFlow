from datetime import timedelta

import fakeredis
import pytest
from audit_log.models import AuditLog
from comment.models import Comments
from django.contrib.contenttypes.models import ContentType
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from notification.models import Notification
from project.models import Project
from task.models import FileUpload, Label, Task
from team.models import Team
from users.models import Profile, Users
from workspace.models import Workspace, WorkspaceInvitation, WorkspaceMember


@pytest.fixture
def profile(db):
    return Profile.objects.create(
        username="Mila",
        first_name="Mila",
        last_name="Mila",
        birth="2026-10-06T11:06:08.887Z",
        image="string",
        bio="string",
    )


@pytest.fixture
def other_profile(db):
    return Profile.objects.create(
        username="Kia",
        first_name="KIa",
        last_name="KIa",
        birth="2026-10-06T11:06:08.887Z",
        image="string",
        bio="string",
    )


@pytest.fixture
def user(db, profile):
    return Users.objects.create_user(
        password="testpass123",
        email="Mila@example.com",
        phone="97777777",
        profile=profile,
    )


@pytest.fixture
def other_user(db, other_profile):
    return Users.objects.create_user(
        password="1",
        email="Kia@example.com",
        phone="97377777",
        profile=other_profile,
    )


@pytest.fixture
def workspace(db, user):
    return Workspace.objects.create(
        name="Redmi",
        description="Testing",
        owner=user,
    )


@pytest.fixture
def other_workspace(db, user):
    return Workspace.objects.create(
        name="Huawei",
        description="Testing",
        owner=user,
    )


@pytest.fixture
def other_workspace_project(db, other_user, other_member):
    workspace = Workspace.objects.create(
        name="Other",
        description="Testing",
        owner=other_user,
    )
    project = Project.objects.create(
        title="Project 2",
        workspace=workspace,
        member=other_member,
        description="Testing",
    )
    return project


@pytest.fixture
def other_member(db, other_workspace, other_user):
    return WorkspaceMember.objects.create(
        workspace=other_workspace,
        user=other_user,
        role=WorkspaceMember.Role.MANAGER,
    )


@pytest.fixture
def member(db, workspace, user):
    return WorkspaceMember.objects.create(
        workspace=workspace,
        user=user,
        role=WorkspaceMember.Role.MANAGER,
    )


@pytest.fixture
def invitation(db, workspace, member):
    return WorkspaceInvitation.objects.create(
        workspace=workspace,
        email="new@example.com",
        invited_by=member,
        expires_at=timezone.now() + timedelta(days=7),
    )


@pytest.fixture
def audit_log(db, member, workspace):
    return AuditLog.objects.create(
        actor=member,
        action="CREATE",
        content_type=ContentType.objects.get_for_model(workspace),
        object_id=workspace.pk,
        old_value=None,
        new_value={"name": "Redmi"},
    )


@pytest.fixture(autouse=True)
def media_root(settings, tmp_path):
    # Test fayllari loyiha papkasiga tushmasligi uchun
    settings.MEDIA_ROOT = tmp_path


@pytest.fixture
def team(db, workspace, user):
    return Team.objects.create(name="Backend", workspace=workspace, team_lead=user)


@pytest.fixture
def project(db, workspace, team, member):
    return Project.objects.create(
        title="Project 1",
        team=team,
        workspace=workspace,
        member=member,
        description="Testing",
    )


@pytest.fixture
def label(db, workspace):
    return Label.objects.create(name="Bug", color="#ff0000", workspace=workspace)


@pytest.fixture
def file_upload(db):
    return FileUpload.objects.create(
        file=SimpleUploadedFile("test.txt", b"hello", content_type="text/plain")
    )


@pytest.fixture
def task(db, project, member):
    return Task.objects.create(
        title="Task 1",
        description="Testing",
        project=project,
        assignee=member,
        reporter=member,
        priority=Task.Priority.HIGH,
    )


@pytest.fixture
def subtask(db, task, project, member):
    return Task.objects.create(
        title="Subtask 1",
        parent=task,
        project=project,
        assignee=member,
        reporter=member,
    )


@pytest.fixture
def comment(db, user, task):
    return Comments.objects.create(author=user, task=task, text="Test comment")


@pytest.fixture
def reply(db, user, task, comment):
    return Comments.objects.create(author=user, task=task, text="Reply", parent=comment)


@pytest.fixture
def notification(db, user, task):
    return Notification.objects.create(
        recipient=user,
        notification_type=Notification.NotificationType.TASK_ASSIGNED,
        title="New task",
        message="Sizga task biriktirildi",
        task=task,
    )


from rest_framework.test import APIClient


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def auth_client(api_client, user):
    api_client.force_authenticate(user=user)
    return api_client


@pytest.fixture
def employee(db, workspace):
    """Oddiy a'zo (EMPLOYEE). (user, member) qaytaradi."""
    u = Users.objects.create_user(email="emp@example.com", phone="976666666", password="x")
    m = WorkspaceMember.objects.create(
        workspace=workspace, user=u, role=WorkspaceMember.Role.EMPLOYEE
    )
    return u, m


@pytest.fixture
def employee_client(api_client, employee):
    api_client.force_authenticate(user=employee[0])
    return api_client


@pytest.fixture
def manager_client(api_client, workspace):
    u = Users.objects.create_user(email="mgr@example.com", phone="977777777", password="x")
    WorkspaceMember.objects.create(
        workspace=workspace, user=u, role=WorkspaceMember.Role.MANAGER
    )
    api_client.force_authenticate(user=u)
    return api_client


@pytest.fixture
def stranger(db):
    return Users.objects.create_user(
        email="stranger@example.com", phone="975555555", password="x"
    )


@pytest.fixture
def ready_task(task):
    """Status o'zgartirishga tayyor: deadline bor."""
    task.deadline = timezone.now() + timedelta(days=3)
    task.save()
    return task


@pytest.fixture
def team_member(db, workspace, team):
    """Team'ga a'zo bo'lgan EMPLOYEE. (user, member) qaytaradi."""
    u = Users.objects.create_user(email="tm@example.com", phone="975555551", password="x")
    m = WorkspaceMember.objects.create(
        workspace=workspace, user=u, role=WorkspaceMember.Role.EMPLOYEE
    )
    m.team.add(team)
    return u, m


@pytest.fixture(autouse=True)
def in_memory_channel_layer(settings):
    settings.CHANNEL_LAYERS = {
        "default": {"BACKEND": "channels.layers.InMemoryChannelLayer"}
    }


@pytest.fixture(autouse=True)
def fake_redis(monkeypatch):
    fake = fakeredis.FakeStrictRedis(decode_responses=True)
    monkeypatch.setattr("shared.utils.redis_client", fake)
    return fake


@pytest.fixture
def admin_client(api_client, db):
    admin = Users.objects.create_superuser(
        email="admin@example.com", phone="972222222", password="x")
    api_client.force_authenticate(user=admin)
    return api_client, admin


@pytest.fixture(autouse=True)
def celery_eager(settings):
    settings.CELERY_TASK_ALWAYS_EAGER = True
    settings.CELERY_TASK_EAGER_PROPAGATES = True


@pytest.fixture
def manager(db, workspace):
    """MANAGER roli. (user, member) qaytaradi."""
    u = Users.objects.create_user(
        email="mgr2@example.com", phone="977777778", password="x")
    m = WorkspaceMember.objects.create(
        workspace=workspace, user=u, role=WorkspaceMember.Role.MANAGER)
    return u, m
