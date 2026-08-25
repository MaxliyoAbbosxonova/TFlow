from django.contrib import admin
from django.contrib.admin import ModelAdmin

from shared.models import FileUpload


# Register your models here.

@admin.register(FileUpload)
class WorkspaceAdmin(ModelAdmin):
    list_display = ('id', 'file', 'uploaded_at')
    list_display_links = ('id', 'file', 'uploaded_at')
