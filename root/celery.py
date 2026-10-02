import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'root.settings')

app = Celery('root')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()


app.conf.beat_schedule = {
    'notify-deadline-tomorrow': {
        'task': 'notification.tasks.notify_upcoming_deadlines',
        'schedule': crontab(hour=9, minute=0) # ertalab 9 da
    },
}