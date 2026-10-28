import pytest
from django.db import IntegrityError
from users.models import Profile, Users

# ---------- UserManager.create_user ----------

def test_create_user_without_email_raises(db):
    with pytest.raises(ValueError, match="Email"):
        Users.objects.create_user(email="", phone="971111111", password="x")


def test_create_user_without_phone_raises(db):
    with pytest.raises(ValueError, match="Telefon"):
        Users.objects.create_user(email="a@example.com", phone="", password="x")


def test_create_user_normalizes_email_domain(db):
    user = Users.objects.create_user(
        email="Test@EXAMPLE.COM", phone="971111111", password="x"
    )
    assert user.email == "Test@example.com"


def test_create_user_hashes_password(db):
    user = Users.objects.create_user(
        email="a@example.com", phone="971111111", password="secret123"
    )
    assert user.password != "secret123"
    assert user.check_password("secret123")


def test_create_user_is_not_staff_or_superuser(user):
    assert user.is_staff is False
    assert user.is_superuser is False


# ---------- UserManager.create_superuser ----------

def test_create_superuser_sets_flags(db):
    admin = Users.objects.create_superuser(
        email="admin@example.com", phone="972222222", password="x"
    )
    assert admin.is_staff is True
    assert admin.is_superuser is True
    assert admin.is_active is True


def test_create_superuser_with_is_staff_false_raises(db):
    with pytest.raises(ValueError, match="is_staff"):
        Users.objects.create_superuser(
            email="admin@example.com", phone="972222222",
            password="x", is_staff=False,
        )


def test_create_superuser_with_is_superuser_false_raises(db):
    with pytest.raises(ValueError, match="is_superuser"):
        Users.objects.create_superuser(
            email="admin@example.com", phone="972222222",
            password="x", is_superuser=False,
        )


# ---------- Users ----------

def test_user_str_returns_email(user):
    assert str(user) == user.email


def test_user_default_status_is_active(user):
    assert user.status == Users.Status.ACTIVE


def test_user_email_must_be_unique(user):
    with pytest.raises(IntegrityError):
        Users.objects.create_user(
            email=user.email, phone="973333333", password="x"
        )


def test_user_has_no_username_field(user):
    assert Users.USERNAME_FIELD == "email"
    assert Users.username is None


def test_user_profile_is_linked(user, profile):
    assert user.profile == profile
    assert profile.user == user


# ---------- Profile ----------

def test_profile_str_returns_username(profile):
    assert str(profile) == profile.username


def test_profile_default_bio_is_empty(db):
    profile = Profile.objects.create(
        username="NoBio", first_name="A", last_name="B"
    )
    assert profile.bio == ""


def test_profile_timestamps_set_automatically(profile):
    assert profile.created_at is not None
    assert profile.updated_at is not None


def test_profile_updated_at_changes_on_save(profile):
    old = profile.updated_at
    profile.bio = "changed"
    profile.save()
    profile.refresh_from_db()
    assert profile.updated_at > old


# ---------- on_delete ----------

def test_user_deleted_when_profile_deleted(user, profile):
    pk = user.pk
    profile.delete()
    assert not Users.objects.filter(pk=pk).exists()


def test_profile_stays_when_user_deleted(user, profile):
    """Hozirgi xatti-harakat: user o'chsa profile qoladi (orphan)."""
    user_pk = user.pk
    user.delete()
    assert not Users.objects.filter(pk=user_pk).exists()
    assert Profile.objects.filter(pk=profile.pk).exists()
