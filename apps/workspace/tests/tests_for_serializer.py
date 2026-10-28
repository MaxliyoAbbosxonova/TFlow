import uuid
from datetime import timedelta
from types import SimpleNamespace

import pytest
from django.utils import timezone
from rest_framework.exceptions import ValidationError
from users.models import Users
from workspace.models import WorkspaceInvitation, WorkspaceMember
from workspace.serializers import (
    CheckTokenSerializer,
    InvitationAcceptModelSerializer,
    InvitationAnonymousAcceptModelSerializer,
    WorkspaceInvitationModelSerializer,
    WorkspaceModelSerializer,
)


def ctx(user):
    """Soxta request: serializer faqat request.user ni o'qiydi."""
    return {"request": SimpleNamespace(user=user)}


# ---------- WorkspaceModelSerializer ----------
def test_workspace_serializer_requires_name(user):
    """ name kiritish majburiy ekanini tekshiradi """

    s = WorkspaceModelSerializer(data={"description": "x"}, context=ctx(user))
    assert not s.is_valid()
    assert "name" in s.errors


def test_workspace_serializer_creates_workspace_with_owner(user):
    """Workspace yaratilganda owner so'rov yuborgan user bo'ladi."""

    s = WorkspaceModelSerializer(
        data={"name": "New", "description": "Desc"}, context=ctx(user)
    )
    assert s.is_valid(), s.errors
    ws = s.save()
    assert ws.name == "New"
    assert ws.owner == user


def test_workspace_creator_becomes_member_of_that_workspace(user):
    """Workspace yaratuvchisi shu workspace'ga WORKSPACE_OWNER rolida a'zo bo'ladi."""

    s = WorkspaceModelSerializer(
        data={"name": "New", "description": "Desc"}, context=ctx(user)
    )
    assert s.is_valid(), s.errors
    ws = s.save()

    member = WorkspaceMember.objects.get(user=user)
    assert member.role == WorkspaceMember.Role.WORKSPACE_OWNER
    assert member.workspace == ws  # <-- bu test hozir YIQILADI (pastga qarang)


# ---------- WorkspaceInvitationModelSerializer ----------

def test_invitation_serializer_sets_invited_by(user, workspace, member):
    """invited_by avtomatik ravishda so'rov yuborgan userning a'zoligiga (WorkspaceMember) o'rnatiladi."""

    s = WorkspaceInvitationModelSerializer(
        data={"workspace": workspace.pk, "email": "x@example.com", "role": "EMPLOYEE"},
        context=ctx(user),
    )
    assert s.is_valid(), s.errors
    assert s.validated_data["invited_by"] == member


def test_invitation_serializer_rejects_non_member(workspace, member):
    """Workspace a'zosi bo'lmagan user taklif yubora olmaydi (validatsiya xatosi)."""
    stranger = Users.objects.create_user(
        email="stranger@example.com", phone="975555555", password="x"
    )
    s = WorkspaceInvitationModelSerializer(
        data={"workspace": workspace.pk, "email": "x@example.com", "role": "EMPLOYEE"},
        context=ctx(stranger),
    )
    assert not s.is_valid()
    assert "non_field_errors" in s.errors


# ---------- CheckTokenSerializer ----------

def test_check_token_valid(invitation, workspace, member):
    """Yaroqli token uchun workspace, invited_by, role va invitation id qaytariladi."""
    s = CheckTokenSerializer(data={"token": str(invitation.token)})
    assert s.is_valid(), s.errors
    assert s.validated_data["workspace"] == workspace.id
    assert s.validated_data["invited_by"] == member.id
    assert s.validated_data["role"] == invitation.role
    assert s.validated_data["invitation"] == invitation.id


def test_check_token_unknown_token_gives_validation_error(db):
    """Mavjud bo'lmagan token 500 emas, validatsiya xatosi beradi."""
    s = CheckTokenSerializer(data={"token": str(uuid.uuid4())})
    assert not s.is_valid()  # <-- hozir AttributeError beradi (pastga qarang)


def test_check_token_expired(invitation):
    """Muddati o'tgan token rad etiladi."""
    invitation.expires_at = timezone.now() - timedelta(minutes=1)
    invitation.save()
    s = CheckTokenSerializer(data={"token": str(invitation.token)})
    assert not s.is_valid()


@pytest.mark.parametrize("status", [
    WorkspaceInvitation.Status.ACCEPTED,
    WorkspaceInvitation.Status.EXPIRED,
    WorkspaceInvitation.Status.REVOKED,
])
def test_check_token_non_pending_status(invitation, status):
    """Statusi PENDING bo'lmagan (accepted/expired/revoked) token rad etiladi."""
    invitation.status = status
    invitation.save()
    s = CheckTokenSerializer(data={"token": str(invitation.token)})
    assert not s.is_valid()


# ---------- InvitationAnonymousAcceptModelSerializer ----------

@pytest.mark.parametrize("raw, expected", [
    ("+998 90 123 45 67", "901234567"),  # 998 prefiksi olinadi
    ("90-123-45-67", "901234567"),  # belgilar tozalanadi
    ("901234567", "901234567"),
])
def test_validate_phone_normalizes(raw, expected):
    """Telefon raqamdan raqamdan boshqa belgilar va '998' prefiksi olib tashlanadi."""
    assert InvitationAnonymousAcceptModelSerializer().validate_phone(raw) == expected


def test_validate_phone_too_short():
    """9 tadan kam raqamli telefon rad etiladi."""
    with pytest.raises(ValidationError):
        InvitationAnonymousAcceptModelSerializer().validate_phone("12345")


def test_anonymous_accept_email_must_match_invitation(invitation):
    """So'rovdagi email taklifdagi email bilan mos kelmasa, rad etiladi."""
    data = {"token": invitation.token, "email": "other@example.com"}
    with pytest.raises(ValidationError):
        InvitationAnonymousAcceptModelSerializer().validate(data)


def test_anonymous_accept_valid(invitation):
    """So'rovdagi email taklifdagi email bilan mos kelsa, ma'lumot o'tadi."""
    data = {"token": invitation.token, "email": invitation.email}
    assert InvitationAnonymousAcceptModelSerializer().validate(data) == data


def test_anonymous_accept_expired(invitation):
    """Muddati o'tgan taklif anonim qabul qilishda rad etiladi."""
    invitation.expires_at = timezone.now() - timedelta(minutes=1)
    invitation.save()
    data = {"token": invitation.token, "email": invitation.email}
    with pytest.raises(ValidationError):
        InvitationAnonymousAcceptModelSerializer().validate(data)


# ---------- InvitationAcceptModelSerializer ----------

def test_accept_valid_when_email_matches_user(invitation, user):
    """Taklif emaili tizimga kirgan user emaili bilan mos kelsa, qabul qilinadi."""
    invitation.email = user.email
    invitation.save()
    s = InvitationAcceptModelSerializer(
        data={"token": str(invitation.token)}, context=ctx(user)
    )
    assert s.is_valid(), s.errors


def test_accept_rejects_other_users_email(invitation, user):
    """Taklif boshqa email uchun bo'lsa, tizimga kirgan user qabul qila olmaydi."""
    # invitation.email = "new@example.com", user.email = "Mila@example.com"
    s = InvitationAcceptModelSerializer(
        data={"token": str(invitation.token)}, context=ctx(user)
    )
    assert not s.is_valid()


def test_accept_rejects_unknown_token(user):
    """Mavjud bo'lmagan token rad etiladi."""
    s = InvitationAcceptModelSerializer(
        data={"token": str(uuid.uuid4())}, context=ctx(user)
    )
    assert not s.is_valid()
