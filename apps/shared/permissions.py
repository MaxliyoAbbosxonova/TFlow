from django.shortcuts import get_object_or_404
from rest_framework.permissions import BasePermission

from workspace.models import Workspace, WorkspaceMember
from project.models import  Project


class PermissionRemove(BasePermission):
    def has_permission(self, request, view):
        w_space_id = view.kwargs.get("w_space_id")

        workspace = get_object_or_404(
            Workspace,
            id=w_space_id
        )

        if request.user.is_staff:
            return True

        if workspace.owner == request.user:
            return True

        return WorkspaceMember.objects.filter(
            user=request.user,
            workspace=workspace,
            role=WorkspaceMember.Role.MANAGER
        ).exists()


class Workspace_Projects_Members(BasePermission):
    def has_permission(self, request, w_space_id):
        if request.method == 'GET':
            return request.user.is_staff or Workspace(id=w_space_id).owner == request.user
        return True


class Projects_Tasks_Members(BasePermission):
    def has_permission(self, request, project_id):
        if request.method == 'GET':
            return request.user.is_staff or Project.objects.filter(team__team_lead=request.user.id).exists()
        return False


class Tasks_Create_Permission(BasePermission):
    def has_permission(self, request, project_id):
        if request.method == 'GET':
            return request.user.is_staff or Project.team.team_lead == request.user
        return True


class Tasks_CRUD_Permission(BasePermission):
    def has_permission(self, request, view):
        if request.method == 'PUT' or request.method == 'PATCH' or request.method == 'DELETE':
            return Project.team.team_lead == request.user or WorkspaceMember(user=request.user, )
