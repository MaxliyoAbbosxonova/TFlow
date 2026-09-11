from celery import shared_task
from django.core.mail import send_mail
from django.db import transaction

from notification.models import Notification


@transaction.atomic
def send_notification(recipient, notification_type, title, message,**kwargs):
    Notification.objects.create(
        recipient=recipient, notification_type=notification_type,
        title=title, message=message,**kwargs
    )

