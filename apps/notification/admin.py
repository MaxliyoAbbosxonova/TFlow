from django.contrib import admin
from django.contrib.admin import ModelAdmin

from notification.models import Notification


# Register your models here.

@admin.register(Notification)
class NotificationAdmin(ModelAdmin):
    list_display = ('id','task','message','comment','recipient')
    list_display_links = ('id','task','recipient')
