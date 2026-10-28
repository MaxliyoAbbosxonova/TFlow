from datetime import timedelta

from django.utils import timezone
from workspace.models import WorkspaceInvitation, WorkspaceMember


def test_str_returns_name(workspace):
    assert str(workspace) == "Redmi"


def test_member_str_returns_user_email(workspace, user, member):
    assert str(member) == "Mila@example.com"


def test_member_default_role_is_employee(workspace, user):
    member = WorkspaceMember.objects.create(workspace=workspace, user=user)
    assert member.role == WorkspaceMember.Role.EMPLOYEE


def test_is_valid_true_when_pending_and_not_expired(invitation):
    assert invitation.is_valid() is True


def test_is_valid_when_expired_by_date(invitation):
    invitation.expires_at = timezone.now() - timedelta(minutes=1)
    invitation.save()
    assert invitation.is_valid() is False


def test_is_valid_false_when_status_not_pending(invitation):
    for status in (
            WorkspaceInvitation.Status.ACCEPTED,
            WorkspaceInvitation.Status.EXPIRED,
            WorkspaceInvitation.Status.REVOKED,
    ):
        invitation.status = status
        assert invitation.is_valid() is False


def test_default_status_is_pending(invitation):
    assert invitation.status == WorkspaceInvitation.Status.PENDING


def test_default_role_is_employee(invitation):
    assert invitation.role == WorkspaceMember.Role.EMPLOYEE


def test_token_is_generated_automatically(invitation):
    assert invitation.token is not None


def test_tokens_are_unique(workspace, member):
    expires = timezone.now() + timedelta(days=7)
    a = WorkspaceInvitation.objects.create(
        workspace=workspace, email="a@example.com", invited_by=member, expires_at=expires
    )
    b = WorkspaceInvitation.objects.create(
        workspace=workspace, email="b@example.com", invited_by=member, expires_at=expires
    )
    assert a.token != b.token


# --- CASCADE ---

def test_invitation_deleted_when_workspace_deleted(invitation, workspace):
    workspace.delete()
    assert not WorkspaceInvitation.objects.filter(pk=invitation.pk).exists()
