from comment.models import Comments
from django.contrib import admin
from django.contrib.admin import ModelAdmin

# Register your models here.


@admin.register(Comments)
class NotificationAdmin(ModelAdmin):
    list_display = ('id', 'task', 'text', 'author', 'parent')
    list_display_links = ('id', 'task', 'author', 'parent')
