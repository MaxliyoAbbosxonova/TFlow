from unittest.mock import patch

from django.urls import reverse

from workspace.models import Workspace, WorkspaceMember, WorkspaceInvitation

# URL nomlarini urls.py dagi name= ga moslang
URL_LIST_CREATE = "workspace-list-create"
URL_CHANGE_OWNER = "workspace-change-owner"  # args: workspace_id, member_id
URL_REMOVE_MEMBER = "workspace-remove-member"  # args: member_id, w_space_id
URL_INVITE = "workspace-invitation-create"
URL_CHECK_TOKEN = "workspace-check-token"  # args: token
URL_ACCEPT = "workspace-invitation-accept"  # args: token


# ---------- Workspace yaratish ----------

def test_create_workspace_requires_auth(api_client):
    r = api_client.post(reverse(URL_LIST_CREATE), {"name": "X", "description": "d"})
    assert r.status_code in (401, 403)


def test_create_workspace_success(auth_client, user):
    r = auth_client.post(
        reverse(URL_LIST_CREATE), {"name": "New", "description": "d"}, format="json"
    )
    assert r.status_code == 201
    ws = Workspace.objects.get(name="New")
    assert ws.owner == user
    assert WorkspaceMember.objects.filter(
        workspace=ws, user=user, role=WorkspaceMember.Role.WORKSPACE_OWNER
    ).exists()


def test_create_workspace_without_name_returns_400(auth_client):
    r = auth_client.post(reverse(URL_LIST_CREATE), {"description": "d"}, format="json")
    assert r.status_code == 400
    assert "name" in r.data


# ---------- Workspace ro'yxati ----------

def test_list_workspaces_superuser_sees_all(api_client, workspace, db):
    from users.models import Users
    admin = Users.objects.create_superuser(
        email="admin@example.com", phone="972222222", password="x"
    )
    api_client.force_authenticate(user=admin)
    r = api_client.get(reverse(URL_LIST_CREATE))
    assert r.status_code == 200


def test_list_workspaces_regular_user_does_not_crash(auth_client, workspace):
    # Hozir 500 beradi: get_queryset oddiy user uchun None qaytaradi
    r = auth_client.get(reverse(URL_LIST_CREATE))
    assert r.status_code == 200


# ---------- Owner almashtirish ----------

def test_change_owner_success(auth_client, user, workspace, member):
    r = auth_client.post(reverse(URL_CHANGE_OWNER, args=[workspace.id, member.id]))
    assert r.status_code == 200


def test_change_owner_by_non_owner_is_rejected(api_client, stranger, workspace, member):
    api_client.force_authenticate(user=stranger)
    r = api_client.post(reverse(URL_CHANGE_OWNER, args=[workspace.id, member.id]))
    assert r.status_code in (400, 403)
    workspace.refresh_from_db()
    assert workspace.owner != stranger


def test_change_owner_member_from_other_workspace(auth_client, workspace, member, user, db):
    other_ws = Workspace.objects.create(name="Other", description="d", owner=user)
    other_member = WorkspaceMember.objects.create(
        workspace=other_ws, user=user, role=WorkspaceMember.Role.EMPLOYEE
    )
    r = auth_client.post(reverse(URL_CHANGE_OWNER, args=[workspace.id, other_member.id]))
    assert r.status_code == 400


# ---------- A'zoni o'chirish ----------

def test_remove_member_success(auth_client, workspace, member):
    r = auth_client.delete(reverse(URL_REMOVE_MEMBER, args=[member.id, workspace.id]))
    assert r.status_code == 200
    assert not WorkspaceMember.objects.filter(pk=member.pk).exists()


def test_remove_member_from_wrong_workspace(auth_client, member, user, db):
    other_ws = Workspace.objects.create(name="Other", description="d", owner=user)
    r = auth_client.delete(reverse(URL_REMOVE_MEMBER, args=[member.id, other_ws.id]))
    assert r.status_code == 400
    assert WorkspaceMember.objects.filter(pk=member.pk).exists()


def test_remove_member_by_stranger_is_forbidden(api_client, stranger, workspace, member):
    # Hozir o'tmaydi: viewda hech qanday ruxsat tekshiruvi yo'q
    api_client.force_authenticate(user=stranger)
    r = api_client.delete(reverse(URL_REMOVE_MEMBER, args=[member.id, workspace.id]))
    assert r.status_code in (403, 404)
    assert WorkspaceMember.objects.filter(pk=member.pk).exists()


# ---------- Taklif yaratish ----------

@patch("workspace.views.create_invitation")
def test_create_invitation_success(mock_create, auth_client, workspace, member, invitation):
    mock_create.return_value = invitation
    r = auth_client.post(
        reverse(URL_INVITE),
        {"workspace": workspace.id, "email": "new@example.com", "role": "EMPLOYEE"},
        format="json",
    )
    assert r.status_code == 200
    assert r.data["data"] == "new@example.com"
    mock_create.assert_called_once()


def test_create_invitation_by_non_member_returns_400(api_client, stranger, workspace, member):
    api_client.force_authenticate(user=stranger)
    r = api_client.post(
        reverse(URL_INVITE),
        {"workspace": workspace.id, "email": "x@example.com", "role": "EMPLOYEE"},
        format="json",
    )
    assert r.status_code == 400


# ---------- Token tekshirish ----------

def test_check_token_valid(auth_client, invitation):
    r = auth_client.get(reverse(URL_CHECK_TOKEN, args=[invitation.token]))
    assert r.status_code == 200
    assert r.data["data"]["role"] == invitation.role


def test_check_token_unknown_returns_400(auth_client, db):
    import uuid
    r = auth_client.get(reverse(URL_CHECK_TOKEN, args=[uuid.uuid4()]))
    assert r.status_code == 400


# ---------- Taklifni qabul qilish ----------

@patch("workspace.views.send_invitation_accept_email_task")
def test_accept_invitation_authenticated(mock_email, api_client, invitation, user):
    invitation.email = user.email
    invitation.save()
    api_client.force_authenticate(user=user)

    r = api_client.post(reverse(URL_ACCEPT, args=[invitation.token]), {}, format="json")

    assert r.status_code == 200
    assert r.data["workspace_id"] == invitation.workspace_id
    mock_email.delay.assert_called_once()


@patch("workspace.views.send_invitation_accept_email_task")
def test_accept_invitation_wrong_email_returns_400(mock_email, auth_client, invitation):
    # invitation.email = new@example.com, user.email = Mila@example.com
    r = auth_client.post(reverse(URL_ACCEPT, args=[invitation.token]), {}, format="json")
    assert r.status_code == 400
    mock_email.delay.assert_not_called()


@patch("workspace.views.send_invitation_accept_email_task")
def test_accept_invitation_anonymous_returns_401(mock_email, api_client, invitation):
    r = api_client.post(reverse(URL_ACCEPT, args=[invitation.token]), {}, format="json")

    assert r.status_code == 401
    assert r.data["message"] == "User Ro'yhatdan o'tmagan"

    invitation.refresh_from_db()
    assert invitation.status == WorkspaceInvitation.Status.PENDING
    assert not WorkspaceMember.objects.filter(workspace=invitation.workspace, user__email=invitation.email).exists()
    mock_email.delay.assert_not_called()
