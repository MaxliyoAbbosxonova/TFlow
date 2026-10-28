from django.urls import reverse
from users.models import Users

PASSWORD = "testpass123"


def login(client, email, password):
    return client.post(reverse("auth-login"), {"email": email, "password": password}, format="json")


def test_login_success_returns_tokens(api_client, user):
    """To'g'ri email va parol: access va refresh token qaytadi."""
    r = login(api_client, user.email, PASSWORD)
    assert r.status_code == 200, r.data
    assert "access" in r.data and "refresh" in r.data
    assert r.data["user"]["email"] == user.email


def test_login_wrong_password_returns_400(api_client, user):
    """Noto'g'ri parol: 400, token yo'q."""
    r = login(api_client, user.email, "wrong")
    assert r.status_code == 400
    assert "access" not in r.data


def test_login_unknown_email_returns_400(api_client, db):
    """Mavjud bo'lmagan email: 400 (xabar parol xatosi bilan bir xil)."""
    r = login(api_client, "nobody@example.com", PASSWORD)
    assert r.status_code == 400


def test_login_error_does_not_reveal_which_field_is_wrong(api_client, user):
    """Email xatosi va parol xatosi bir xil xabar beradi (user enumeration oldini olish)."""
    a = login(api_client, user.email, "wrong")
    b = login(api_client, "nobody@example.com", "wrong")
    assert a.data == b.data


def test_blocked_user_cannot_login(api_client, user):
    """BLOCKED foydalanuvchi kira olmaydi."""
    Users.objects.filter(pk=user.pk).update(status=Users.Status.BLOCKED)
    r = login(api_client, user.email, PASSWORD)
    assert r.status_code == 400
    assert "access" not in r.data


def test_login_long_password_works(api_client, db):
    """8 belgidan uzun parol bilan login ishlaydi."""
    Users.objects.create_user(email="long@example.com", phone="971112233", password="averylongpassword123")
    r = login(api_client, "long@example.com", "averylongpassword123")
    assert r.status_code == 200, r.data


# ----------------------------------------------------Register


from users.models import Profile


def register_payload(**overrides):
    data = {
        "email": "new@example.com",
        "phone": "971112200",
        "password": "newpass12345",
        "profile": {"username": "newbie", "first_name": "New", "last_name": "User"},
    }
    data.update(overrides)
    return data


def register(client, **overrides):
    return client.post(reverse("auth-register"), register_payload(**overrides), format="json")


def test_register_success_returns_tokens(api_client, db):
    """Muvaffaqiyatli ro'yxatdan o'tishda access va refresh token qaytadi."""
    r = register(api_client)
    assert r.status_code == 200, r.data
    assert "access" in r.data and "refresh" in r.data


def test_register_creates_user_with_linked_profile(api_client, db):
    """User va unga bog'langan Profile bazada yaratiladi."""
    register(api_client)
    user = Users.objects.get(email="new@example.com")
    assert user.profile is not None
    assert user.profile.username == "newbie"
    assert user.phone == "971112200"


def test_register_hashes_password(api_client, db):
    """Parol ochiq matnda saqlanmaydi."""
    register(api_client)
    user = Users.objects.get(email="new@example.com")
    assert user.password != "newpass12345"
    assert user.check_password("newpass12345")


def test_register_duplicate_phone_returns_400(api_client, user):
    """Band telefon raqam bilan ro'yxatdan o'tib bo'lmaydi."""
    r = register(api_client, phone=user.phone)
    assert r.status_code == 400
    assert "phone" in r.data
    assert not Users.objects.filter(email="new@example.com").exists()


def test_register_duplicate_email_returns_400(api_client, user):
    """Band email bilan ro'yxatdan o'tib bo'lmaydi."""
    r = register(api_client, email=user.email)
    assert r.status_code == 400
    assert Users.objects.filter(email=user.email).count() == 1


def test_register_failure_leaves_no_orphan_profile(api_client, user):
    """Rad etilgan ro'yxatdan o'tish yetim Profile qoldirmaydi."""
    before = Profile.objects.count()
    register(api_client, phone=user.phone)
    assert Profile.objects.count() == before


def test_registered_user_can_login(api_client, db):
    """Ro'yxatdan o'tgan foydalanuvchi o'sha parol bilan kira oladi."""
    register(api_client)
    r = login(api_client, "new@example.com", "newpass12345")
    assert r.status_code == 200, r.data


from shared.utils import check_sms_code, send_sms_code


def reset(client, email, new_pass):
    return client.post(
        reverse("auth-p_reset"),
        {"email": email, "new_pass": new_pass},
        format="json",
    )


def verify_email(email):
    code = send_sms_code(email)["code"]
    assert check_sms_code(email, code) is True


def test_reset_without_verification_is_rejected(api_client, user):
    """Kod tasdiqlanmasa parol o'zgarmaydi (400)."""
    r = reset(api_client, user.email, "brandnew123")
    assert r.status_code == 400
    user.refresh_from_db()
    assert user.check_password("testpass123")


def test_reset_changes_password(api_client, user):
    """Tasdiqlangan email uchun parol o'zgaradi."""
    verify_email(user.email)
    r = reset(api_client, user.email, "brandnew123")
    assert r.status_code == 200, r.data
    assert login(api_client, user.email, "brandnew123").status_code == 200


def test_reset_is_one_time_only(api_client, user):
    """Parol o'zgargach tasdiqlash bekor bo'ladi: ikkinchi urinish rad etiladi."""
    verify_email(user.email)
    assert reset(api_client, user.email, "brandnew123").status_code == 200
    assert reset(api_client, user.email, "another456").status_code == 400
    assert login(api_client, user.email, "brandnew123").status_code == 200


def test_reset_response_does_not_leak_password(api_client, user):
    verify_email(user.email)
    r = reset(api_client, user.email, "brandnew123")
    assert "new_pass" not in r.data


def test_send_code_twice_is_rate_limited(api_client, user, mailoutbox):
    """Kod muddati tugamaguncha ikkinchi so'rov 429 beradi."""
    url = reverse("auth-send_code")
    assert api_client.post(url, {"email": user.email}, format="json").status_code == 200
    assert api_client.post(url, {"email": user.email}, format="json").status_code == 429


def test_wrong_code_is_rejected_and_counts_attempts(api_client, user, fake_redis):
    send_sms_code(user.email)
    r = api_client.post(reverse("auth-check_code"),
                        {"email": user.email, "code": 1}, format="json")
    assert r.status_code == 400
    assert fake_redis.hget(f"login:{user.email}", "attempts") == "1"


def test_code_blocked_after_max_attempts(api_client, user):
    code = send_sms_code(user.email)["code"]
    for _ in range(5):
        check_sms_code(user.email, 1)
    assert check_sms_code(user.email, code) is False


def token_pair(client, user):
    r = login(client, user.email, PASSWORD)
    return r.data["access"], r.data["refresh"]


# ---------- Himoyalangan endpoint ----------

def test_protected_endpoint_without_token_rejected(api_client, db):
    """Tokensiz so'rov rad etiladi (401)."""
    assert api_client.get(reverse("auth-p_crud")).status_code in (401, 403)


def test_protected_endpoint_with_invalid_token_rejected(api_client, db):
    """Yaroqsiz token rad etiladi (401)."""
    api_client.credentials(HTTP_AUTHORIZATION="Bearer garbage.token.value")
    assert api_client.get(reverse("auth-p_crud")).status_code == 401


def test_my_profile_with_valid_token(api_client, user):
    """Haqiqiy access token bilan o'z profilini ko'radi."""
    access, _ = token_pair(api_client, user)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
    r = api_client.get(reverse("auth-p_crud"))
    assert r.status_code == 200, r.data
    assert r.data["username"] == user.profile.username


def test_my_profile_patch_updates_only_own_profile(api_client, user):
    access, _ = token_pair(api_client, user)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
    r = api_client.patch(reverse("auth-p_crud"), {"bio": "salom"}, format="json")
    assert r.status_code == 200, r.data
    user.profile.refresh_from_db()
    assert user.profile.bio == "salom"


# ---------- Logout ----------

def test_logout_blacklists_refresh_token(api_client, user):
    """Logoutdan keyin refresh token ishlamaydi."""
    access, refresh = token_pair(api_client, user)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
    r = api_client.post(reverse("auth-logout"), {"refresh": refresh}, format="json")
    assert r.status_code == 204
    again = api_client.post(reverse("auth-logout"), {"refresh": refresh}, format="json")
    assert again.status_code == 400


def test_logout_with_invalid_refresh_returns_400(api_client, user):
    access, _ = token_pair(api_client, user)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
    r = api_client.post(reverse("auth-logout"), {"refresh": "bad"}, format="json")
    assert r.status_code == 400


def test_logout_requires_authentication(api_client, db):
    r = api_client.post(reverse("auth-logout"), {"refresh": "x"}, format="json")
    assert r.status_code in (401, 403)


# ---------- Change status (faqat admin) ----------

def status_url(user):
    return reverse("auth-status", args=[user.id])


def test_admin_can_block_user(admin_client, user):
    """Admin foydalanuvchini bloklay oladi."""
    client, _ = admin_client
    r = client.patch(status_url(user), {"status": "BLOCKED"}, format="json")
    assert r.status_code == 200, r.data
    user.refresh_from_db()
    assert user.status == Users.Status.BLOCKED


def test_regular_user_cannot_change_status(auth_client, stranger):
    """Oddiy foydalanuvchi status o'zgartira olmaydi (403)."""
    r = auth_client.patch(status_url(stranger), {"status": "BLOCKED"}, format="json")
    assert r.status_code == 403
    stranger.refresh_from_db()
    assert stranger.status == Users.Status.ACTIVE


def test_anonymous_cannot_change_status(api_client, user):
    r = api_client.patch(status_url(user), {"status": "BLOCKED"}, format="json")
    assert r.status_code in (401, 403)


def test_admin_cannot_block_self(admin_client):
    """Admin o'zini bloklay olmaydi (400)."""
    client, admin = admin_client
    r = client.patch(status_url(admin), {"status": "BLOCKED"}, format="json")
    assert r.status_code == 400


def test_invalid_status_value_returns_400(admin_client, user):
    client, _ = admin_client
    assert client.patch(status_url(user), {"status": "NOPE"}, format="json").status_code == 400


def test_blocked_user_cannot_login_after_admin_blocks(admin_client, user):
    """Admin bloklagach foydalanuvchi kira olmaydi."""
    client, _ = admin_client
    client.patch(status_url(user), {"status": "BLOCKED"}, format="json")
    client.force_authenticate(user=None)
    assert login(client, user.email, PASSWORD).status_code == 400


# ---------- Admin ro'yxatlari ----------
def test_users_list_admin_only(admin_client):
    client, _ = admin_client
    assert client.get(reverse("auth-list")).status_code == 200


def test_users_list_forbidden_for_regular_user(auth_client):
    assert auth_client.get(reverse("auth-list")).status_code == 403


def test_profiles_list_forbidden_for_regular_user(auth_client):
    assert auth_client.get(reverse("auth-p_list")).status_code == 403
