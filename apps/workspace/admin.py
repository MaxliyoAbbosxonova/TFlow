from django.contrib import admin
from django.contrib.admin import ModelAdmin
from workspace.models import Workspace, WorkspaceInvitation, WorkspaceMember

# Register your models here.


@admin.register(Workspace)
class WorkspaceAdmin(ModelAdmin):
    list_display = ('id', 'name', 'logo', 'owner')
    list_display_links = ('owner', 'id', 'name')


@admin.register(WorkspaceMember)
class WorkspaceMemberAdmin(ModelAdmin):
    list_display = ('id', 'user', 'role', 'workspace')
    list_display_links = ('id',)


@admin.register(WorkspaceInvitation)
class WorkspaceInvitationAdmin(ModelAdmin):
    list_display = ('id', 'workspace', 'role', 'invited_by', 'status', 'expires_at')
    list_display_links = ('id', 'workspace', 'role')
