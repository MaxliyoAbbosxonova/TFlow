import pytest
from django.db import IntegrityError
from django.db.models import RestrictedError
from project.models import Project
from team.models import Team
from workspace.models import WorkspaceMember

""" Project modeli uchun testlar """


def test_team_cannot_be_deleted_while_it_has_projects(team, project):
    with pytest.raises(RestrictedError):
        team.delete()
    assert Project.objects.filter(pk=project.id).exists()
    assert Team.objects.filter(pk=team.id).exists()


def test_project_delete_when_workspace_deleting(workspace, project):
    pk = project.id
    workspace.delete()
    assert not Project.objects.filter(id=pk).exists()


def test_member_cannot_be_deleted_while_assigned_to_project(project, member):
    with pytest.raises(RestrictedError) as exc:
        member.delete()
    assert project in exc.value.restricted_objects
    assert WorkspaceMember.objects.filter(id=member.id).exists()
    assert Project.objects.filter(id=project.id).exists()


def test_project_title_must_be_unique(project, workspace, team, member):
    with pytest.raises(IntegrityError):
        Project.objects.create(
            title=project.title, workspace=workspace, team=team, member=member
        )


def test_start_date_is_set_automatically(project):
    assert project.start_date is not None


def test_default_status_is_planned(project):
    assert project.status == Project.Status.PLANNED


def test_str_returns_title(project):
    assert str(project) == project.title
