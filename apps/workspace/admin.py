from django.contrib import admin
from django.contrib.admin import ModelAdmin

from workspace.models import Workspace, WorkspaceMember, Team, Task, Project


# Register your models here.


@admin.register(Workspace)
class WorkspaceAdmin(ModelAdmin):
    list_display = ('id', 'name', 'logo', 'owner')
    list_display_links = ('owner', 'id', 'name')


@admin.register(WorkspaceMember)
class WorkspaceMemberAdmin(ModelAdmin):
    list_display = ('id', 'user', 'role')
    list_display_links = ('id',)


@admin.register(Team)
class TeamAdmin(ModelAdmin):
    list_display = ('id', 'name')
    list_display_links = ('id', 'name')


@admin.register(Task)
class TaskAdmin(ModelAdmin):
    list_display = ('id', 'title', 'assignee', 'reporter', 'deadline', 'status')
    list_display_links = ('id', 'title', 'assignee', 'reporter')


@admin.register(Project)
class ProjectAdmin(ModelAdmin):
    list_display = ('id', 'title', 'team', 'member', 'status', 'deadline')
    list_display_links = ('title', 'id', 'team', 'member')
