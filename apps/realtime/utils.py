from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.db import transaction


def emit_to_project(project_id, event, data):
    layer = get_channel_layer()
    group = f"project_{project_id}"

    def _send():
        async_to_sync(layer.group_send)(
            group, {"type": "project.event", "data": {"event": event, "data": data}}
        )

    transaction.on_commit(_send)