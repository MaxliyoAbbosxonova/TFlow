import pytest
from asgiref.sync import sync_to_async
from channels.db import database_sync_to_async
from channels.layers import get_channel_layer
from channels.routing import URLRouter
from channels.testing import WebsocketCommunicator
from django.contrib.auth.models import AnonymousUser
from realtime.routing import websocket_urlpatterns
from realtime.utils import emit_to_project

application = URLRouter(websocket_urlpatterns)


def make_communicator(project_id, user):
    comm = WebsocketCommunicator(application, f"ws/projects/{project_id}/")
    comm.scope["user"] = user
    return comm


async def test_anonymous_is_rejected():
    """Login qilmagan foydalanuvchi ulana olmaydi (kod 4401)."""
    comm = make_communicator(1, AnonymousUser())
    connected, code = await comm.connect()
    assert connected is False
    assert code == 4401


from users.models import Users
from workspace.models import WorkspaceMember


def make_user(email, phone):
    return Users.objects.create_user(email=email, phone=phone, password="x")


@pytest.mark.django_db(transaction=True)
async def test_owner_can_connect(project, user):
    """Workspace owner ulana oladi."""
    comm = make_communicator(project.id, user)
    connected, _ = await comm.connect()
    assert connected is True
    await comm.disconnect()


@pytest.mark.django_db(transaction=True)
async def test_stranger_is_rejected(project, stranger):
    """Workspace bilan aloqasi yo'q user rad etiladi (4403)."""
    comm = make_communicator(project.id, stranger)
    connected, code = await comm.connect()
    assert connected is False
    assert code == 4403


@pytest.mark.django_db(transaction=True)
async def test_unknown_project_is_rejected(user):
    """Mavjud bo'lmagan project uchun 4403."""
    comm = make_communicator(999999, user)
    connected, code = await comm.connect()
    assert connected is False
    assert code == 4403


@pytest.mark.django_db(transaction=True)
async def test_employee_is_rejected(project, employee):
    """Oddiy EMPLOYEE (team a'zosi emas) ulana olmaydi (4403)."""
    user, _ = employee
    comm = make_communicator(project.id, user)
    connected, code = await comm.connect()
    assert connected is False
    assert code == 4403


@pytest.mark.django_db(transaction=True)
async def test_manager_can_connect(project, workspace):
    mgr = await database_sync_to_async(make_user)("m@example.com", "976000002")
    await database_sync_to_async(WorkspaceMember.objects.create)(
        workspace=workspace, user=mgr, role=WorkspaceMember.Role.MANAGER)
    comm = make_communicator(project.id, mgr)
    connected, _ = await comm.connect()
    assert connected is True
    await comm.disconnect()


@pytest.mark.django_db(transaction=True)
async def test_emit_to_project_reaches_connected_client(project, user):
    """emit_to_project chaqirilganda ulangan a'zo eventni oladi."""
    comm = make_communicator(project.id, user)
    connected, _ = await comm.connect()
    assert connected is True

    await sync_to_async(emit_to_project)(
        project.id, "task:status_changed", {"task_id": 7}
    )

    message = await comm.receive_json_from(timeout=2)
    assert message == {"event": "task:status_changed", "data": {"task_id": 7}}
    await comm.disconnect()


@pytest.mark.django_db(transaction=True)
async def test_emit_to_other_project_is_not_received(project, user):
    """Boshqa project'ga yuborilgan event bizga kelmaydi."""
    comm = make_communicator(project.id, user)
    await comm.connect()

    await sync_to_async(emit_to_project)(project.id + 999, "x", {})

    assert await comm.receive_nothing(timeout=0.5) is True
    await comm.disconnect()


@pytest.mark.django_db(transaction=True)
async def test_connected_client_receives_event(project, user):
    """Ulangan a'zo project eventini oladi."""
    comm = make_communicator(project.id, user)
    connected, _ = await comm.connect()
    assert connected is True

    layer = get_channel_layer()
    await layer.group_send(
        f"project_{project.id}",
        {
            "type": "project.event",
            "data": {
                "event": "task:status_changed",
                "data": {"task_id": 1},
            },
        },
    )

    message = await comm.receive_json_from(timeout=2)
    assert message["event"] == "task:status_changed"
    assert message["data"]["task_id"] == 1
    await comm.disconnect()


@pytest.mark.django_db(transaction=True)
async def test_event_for_other_project_is_not_received(project, user):
    """Boshqa project eventi kelmaydi."""
    comm = make_communicator(project.id, user)
    await comm.connect()

    layer = get_channel_layer()
    await layer.group_send(f"project_{project.id + 999}",
                           {
                               "type": "project.event",
                               "data": {
                                   "event": "task:status_changed",
                                   "data": {"task_id": 1},
                               },
                           },
                           )
    assert await comm.receive_nothing(timeout=0.5) is True
    await comm.disconnect()


@pytest.mark.django_db(transaction=True)
async def test_client_cannot_broadcast(project, user):
    """Mijoz yuborgan xabar boshqalarga tarqalmaydi."""
    a = make_communicator(project.id, user)
    b = make_communicator(project.id, user)
    await a.connect()
    await b.connect()

    await a.send_json_to({"event": "fake"})

    assert await b.receive_nothing(timeout=0.5) is True
    await a.disconnect()
    await b.disconnect()
