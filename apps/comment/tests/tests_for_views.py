import pytest
from comment.models import Comments
from django.urls import reverse
from task.models import Task

# urls.py dagi name= ga moslang
URL_LIST = "comments-list"  # args: task_id
URL_CREATE = "comments-create"
URL_DETAIL = "comments-detail"  # args: pk (permission task_id ham talab qilsa, uni ham qo'shing)
URL_REPLY = "comments-reply"


"""Comment View file uchun test"""

@pytest.fixture
def stranger_comment(db, stranger, task):
    return Comments.objects.create(author=stranger, task=task, text="Begona")


# ---------- Ro'yxat ----------

def test_list_returns_comments_of_task(auth_client, task, comment):
    """Task kommentlari ro'yxati qaytariladi."""
    r = auth_client.get(reverse(URL_LIST, args=[task.id]))
    assert r.status_code == 200, r.data
    assert [c["id"] for c in r.data] == [comment.id]


def test_list_unknown_task_returns_404(auth_client, db):
    """Mavjud bo'lmagan task uchun 404 qaytariladi."""
    r = auth_client.get(reverse(URL_LIST, args=[999999]))
    assert r.status_code == 404


def test_list_anonymous_is_rejected(api_client, task, comment):
    """Login qilmagan foydalanuvchi kommentlarni ko'ra olmaydi."""
    r = api_client.get(reverse(URL_LIST, args=[task.id]))
    assert r.status_code in (401, 403)


# ---------- Yaratish ----------

def test_create_sets_author_to_request_user(auth_client, user, task):
    """Komment muallifi so'rov yuborgan user bo'ladi."""
    r = auth_client.post(
        reverse(URL_CREATE), {"task": task.id, "text": "Salom"}, format="json"
    )
    assert r.status_code == 201, r.data
    assert Comments.objects.get(id=r.data["id"]).author == user


def test_create_ignores_author_sent_by_client(auth_client, user, stranger, task):
    """Mijoz yuborgan author e'tiborga olinmaydi."""
    r = auth_client.post(
        reverse(URL_CREATE),
        {"task": task.id, "text": "Salom", "author": stranger.id},
        format="json",
    )
    assert r.status_code == 201, r.data
    assert Comments.objects.get(id=r.data["id"]).author == user


def test_create_anonymous_is_rejected(api_client, task):
    """Login qilmagan foydalanuvchi komment yoza olmaydi."""
    r = api_client.post(
        reverse(URL_CREATE), {"task": task.id, "text": "Salom"}, format="json"
    )
    assert r.status_code in (401, 403)
    assert not Comments.objects.exists()


def test_create_by_non_member_is_rejected(api_client, stranger, task):
    """Workspace a'zosi bo'lmagan user komment yoza olmaydi."""
    api_client.force_authenticate(user=stranger)
    r = api_client.post(
        reverse(URL_CREATE), {"task": task.id, "text": "Salom"}, format="json"
    )
    assert r.status_code == 400
    assert not Comments.objects.exists()


# ---------- Retrieve / Update / Delete ----------

def test_author_can_retrieve_own_comment(auth_client, comment):
    """Muallif o'z kommentini ko'ra oladi."""
    r = auth_client.get(reverse(URL_DETAIL, args=[comment.id]))
    assert r.status_code == 200, r.data
    assert r.data["id"] == comment.id


def test_cannot_retrieve_other_users_comment(auth_client, stranger_comment):
    """Boshqa odamning kommenti 404 qaytaradi (queryset faqat o'zinikini beradi)."""
    r = auth_client.get(reverse(URL_DETAIL, args=[stranger_comment.id]))
    assert r.status_code == 404


def test_author_can_update_own_comment(auth_client, comment):
    """Muallif o'z kommenti matnini o'zgartira oladi."""
    r = auth_client.patch(
        reverse(URL_DETAIL, args=[comment.id]), {"text": "Yangi"}, format="json"
    )
    assert r.status_code == 200, r.data
    comment.refresh_from_db()
    assert comment.text == "Yangi"


def test_author_can_delete_own_comment(auth_client, comment):
    """Muallif o'z kommentini o'chira oladi."""
    r = auth_client.delete(reverse(URL_DETAIL, args=[comment.id]))
    assert r.status_code == 204
    assert not Comments.objects.filter(pk=comment.pk).exists()


def test_cannot_delete_other_users_comment(auth_client, stranger_comment):
    """Boshqa odamning kommentini o'chirib bo'lmaydi."""
    r = auth_client.delete(reverse(URL_DETAIL, args=[stranger_comment.id]))
    assert r.status_code in (403, 404)
    assert Comments.objects.filter(pk=stranger_comment.pk).exists()


# ---------- Reply ----------

def test_reply_creates_child_comment(auth_client, user, task, comment):
    """Reply parent'ga bog'langan va muallifi request.user bo'lgan komment yaratadi."""
    r = auth_client.post(
        reverse(URL_REPLY),
        {"task": task.id, "text": "Javob", "parent": comment.id},
        format="json",
    )
    assert r.status_code == 201, r.data
    reply = Comments.objects.get(id=r.data["id"])
    assert reply.parent == comment
    assert reply.author == user
    assert r.data["author"] == user.id


def test_reply_to_comment_of_other_task_returns_400(
        auth_client, comment, project, member
):
    """Parent boshqa taskdagi komment bo'lsa, reply rad etiladi."""
    other = Task.objects.create(
        title="Other", project=project, assignee=member, reporter=member
    )
    r = auth_client.post(
        reverse(URL_REPLY),
        {"task": other.id, "text": "Bad", "parent": comment.id},
        format="json",
    )
    assert r.status_code == 400
