import pytest
from django.db import IntegrityError
from django.db.models import RestrictedError
from team.models import Team


def test_str_returns_name(team):
    assert str(team) == team.name


def test_team_name_must_be_unique(team, workspace, user):
    with pytest.raises(IntegrityError):
        Team.objects.create(name=team.name, workspace=workspace, team_lead=user)


def test_team_deleted_when_workspace_deleted(team, workspace):
    pk = team.pk
    workspace.delete()
    assert not Team.objects.filter(pk=pk).exists()


def test_user_cannot_be_deleted_while_team_lead(team, user):
    with pytest.raises(RestrictedError) as exc:
        user.delete()

    assert team in exc.value.restricted_objects
    assert Team.objects.filter(pk=team.pk).exists()


def test_team_lead_can_be_empty(workspace):
    team = Team.objects.create(name="No lead", workspace=workspace)
    assert team.team_lead is None
