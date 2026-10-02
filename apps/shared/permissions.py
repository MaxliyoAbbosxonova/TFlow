# permissions.py
from django.shortcuts import get_object_or_404
from rest_framework.permissions import BasePermission, SAFE_METHODS

from project.models import Project
from task.models import Task
from team.models import Team
from workspace.models import Workspace, WorkspaceMember


class BaseAuthPermission(BasePermission):
    """Umumiy yordamchi: login tekshiruvi + obyektni bir marta keshlash."""

    def _is_authed(self, request):
        return bool(request.user and request.user.is_authenticated)

    def _get_workspace(self, view):
        if not hasattr(view, "_cached_workspace"):
            view._cached_workspace = get_object_or_404(
                Workspace, id=view.kwargs.get("w_space_id")
            )
        return view._cached_workspace

    def _get_project(self, view):
        if not hasattr(view, "_cached_project"):
            view._cached_project = get_object_or_404(
                Project.objects.select_related("team"),
                id=view.kwargs.get("project_id"),
            )
        return view._cached_project


class PermissionRemove(BaseAuthPermission):
    """
    Workspace a'zolarini boshqarish: admin, workspace egasi yoki MANAGER.
    (Sizning PermissionRemove — tuzatilgan holda)
    """

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False

        if request.user.is_staff:
            return True

        workspace = get_object_or_404(
            Workspace, id=view.kwargs.get("w_space_id")
        )

        if workspace.owner_id == request.user.id:
            return True

        return WorkspaceMember.objects.filter(
            user=request.user,
            workspace=workspace,
            role=WorkspaceMember.Role.MANAGER,
        ).exists()


class Workspace_Projects_Members(BaseAuthPermission):
    """Workspace_Projects_Members — tuzatilgan."""

    def has_permission(self, request, view):
        if not self._is_authed(request):
            return False
        if request.user.is_staff:
            return True

        workspace = self._get_workspace(view)
        return workspace.owner_id == request.user.id


class Projects_Tasks_Members(BaseAuthPermission):
    """Projects_Tasks_Members / Tasks_Create_Permission — tuzatilgan."""

    def has_permission(self, request, view):
        if not self._is_authed(request):
            return False
        if request.user.is_staff:
            return True

        project = self._get_project(view)
        return project.team and project.team.team_lead_id == request.user.id


class Tasks_CRUD_Permission(BaseAuthPermission):
    """
    O'qish — workspace a'zolariga.
    O'zgartirish/o'chirish — team lead, workspace egasi yoki admin.
    (Tasks_CRUD_Permission — tuzatilgan)
    """

    def has_permission(self, request, view):
        if not self._is_authed(request):
            return False
        if request.user.is_staff:
            return True

        project = self._get_project(view)
        workspace = project.workspace  # model tuzilishingizga qarab moslang

        is_member = WorkspaceMember.objects.filter(
            user=request.user, workspace=workspace
        ).exists()

        if request.method in SAFE_METHODS:
            return is_member or workspace.owner_id == request.user.id

        return (
                workspace.owner_id == request.user.id
                or (project.team and project.team.team_lead_id == request.user.id)
        )

class IsOwnerManagerAdmin(BasePermission):
    def has_permission(self, request,view):
        team = get_object_or_404(
            Team, id=view.kwargs.get("pk"))
        if request.method == "GET":
            return request.user.is_staff
        elif request.method in ("POST", "PATCH", "PUT", "DELETE"):
            if team.workspace.owner==request.user  :
                return True
            if WorkspaceMember.objects.filter(user=request.user,role=WorkspaceMember.Role.MANAGER,workspace=team.workspace).exists():
                return True
        return False

class IsOwnerManagerFormLabel(BasePermission):
    def has_permission(self, request, view):
        if request.user.is_superuser:
            return True

        task_id = request.data.get('task_id')
        if not task_id:
            return False

        task = get_object_or_404(Task, id=task_id)
        workspace = task.project.workspace
        team = task.project.team

        # Workspace owner
        if workspace.owner == request.user:
            return True

        # Team lead
        if team and team.team_lead == request.user:
            return True

        # Manager (WorkspaceMember orqali)
        if WorkspaceMember.objects.filter(
            user=request.user,
            workspace=workspace,
            role=WorkspaceMember.Role.MANAGER
        ).exists():
            return True

        return False

class IsOwnerManagerAdminForLISTTEAMS(BasePermission):
    def has_permission(self, request,view):
        workspace = get_object_or_404(
            Workspace, id=view.kwargs.get("pk"))
        return (
                Workspace.objects.filter(
                    id=workspace.id, owner=request.user
                ).exists()
                or WorkspaceMember.objects.filter(
            workspace_id=workspace.id,
            user=request.user,
            role=WorkspaceMember.Role.MANAGER,
        ).exists()
        )

class IsTeamLeadOrEmployee(BasePermission):
    def has_permission(self, request, view):
        task=get_object_or_404(Task,id=view.kwargs.get("task_id"))
        if request.method == "GET":
            return request.user.is_staff
        elif request.method == "POST" or request.method == "PATCH" or request.method == "PUT":
            if (task.project.team.team_lead  == request.user):
                return True
            if WorkspaceMember.objects.filter(user=request.user,role=WorkspaceMember.Role.EMPLOYEE,workspace=task.project.workspace).exists():
                return True
        return None

class IsProjectWorkspaceMember(BasePermission):
    def has_permission(self, request, view):
        project=get_object_or_404(Project,id=view.kwargs.get('pk'))
        if project.team.members.filter(user=request.user).exists() or project.member.user==request.user:
            return True
        return request.user.is_staff




class IsTeamLeadOrManager(BasePermission):
    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False

        if user.is_staff:
            return True

        task = get_object_or_404(
            Task.objects.select_related("project__workspace"),
            id=view.kwargs.get("task_id"),
        )
        project = task.project
        if project.team.filter(team_lead=user).exists():
            return True

        return WorkspaceMember.objects.filter(
            user=user,
            role=WorkspaceMember.Role.MANAGER,
            workspace=project.workspace,
        ).exists()


class IsMemberForComment(BasePermission):
    def has_permission(self, request, view):
        task=get_object_or_404(Task,id=view.kwargs.get("task_id"))
        if request.method == "GET":
            return True
        elif request.method == "POST" or request.method == "PATCH" or request.method == "PUT":
            if (task.project.team.team_lead  == request.user) or task.project.workspace.owner:
                return True
            if WorkspaceMember.objects.filter(user=request.user,role__in=[WorkspaceMember.Role.EMPLOYEE,WorkspaceMember.Role.MANAGER,WorkspaceMember.Role.ADMIN],workspace=task.project.workspace).exists():
                return True
        return None

