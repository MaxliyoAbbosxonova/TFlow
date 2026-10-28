from django.urls import reverse
from pytest_django.fixtures import django_capture_on_commit_callbacks
from users.models import Profile, Users


def test_mention_sends_email_to_mentioned_user(
        auth_client, task, mailoutbox, django_capture_on_commit_callbacks):
    """Kommentda @username yozilsa, o'sha foydalanuvchiga email ketadi."""
    p = Profile.objects.create(username="vali", first_name="V", last_name="V")
    Users.objects.create_user(email="vali@example.com", phone="975551111",
                              password="x", profile=p)

    with django_capture_on_commit_callbacks(execute=True):
        auth_client.post(reverse("comments-create"),
                         {"task": task.id, "text": "Salom @vali"}, format="json")

    assert len(mailoutbox) == 1
    assert mailoutbox[0].to == ["vali@example.com"]
