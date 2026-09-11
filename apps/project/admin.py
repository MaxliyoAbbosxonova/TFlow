from django.contrib import admin
from django.contrib.admin import ModelAdmin

from project.models import Project


# Register your models here.

@admin.register(Project)
class ProjectAdmin(ModelAdmin):
    list_display = ('id', 'title', 'team', 'member', 'status', 'deadline')
    list_display_links = ('title', 'id', 'team', 'member')


