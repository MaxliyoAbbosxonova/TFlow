import pytest
from django.core.exceptions import ValidationError
from django.db.models import RestrictedError
from project.models import Project
from task.models import Label, Task
from workspace.models import WorkspaceMember


def test_default_title_is(task1):
    assert task1.title == "improvement"


def test_default_description_is(task1):
    assert task1.description == "Improve bugs"


def test_member_cannot_be_deleted_while_assigned_to_task(task, member):
    with pytest.raises(RestrictedError):
        member.delete()
    assert WorkspaceMember.objects.filter(id=member.id).exists()
    assert Task.objects.filter(id=task.id).exists()


def test_task_delete_when_project_deleting(task, project):
    pk = task.id
    project.delete()
    assert not Task.objects.filter(id=pk).exists()


def test_task_file_set_to_null_when_file_deleted(task, file_upload):
    task.file = file_upload
    task.save()

    file_upload.delete()

    task.refresh_from_db()
    assert task.file is None
    assert Task.objects.filter(pk=task.pk).exists()


def test_default_priority_is(task1):
    assert task1.priority == Task.Priority.LOW


def test_default_status_is(task1):
    assert task1.status == Task.Workflow.TODO


def test_str_returns_title(task):
    assert str(task) == "Task 1"


def test_subtask_parent_must_be_in_same_project(task, member, workspace, team):
    other = Project.objects.create(
        title="Other", workspace=workspace, team=team, member=member
    )
    with pytest.raises(ValidationError):
        Task.objects.create(
            title="Bad", parent=task, project=other,
            assignee=member, reporter=member,
        )


def test_subtask_in_same_project_is_valid(subtask, task):
    assert subtask.parent == task


def test_task_label_many_to_many(task, label):
    task.label.add(label)
    assert label in task.label.all()


def test_reporter_cannot_be_deleted_while_reporting_task(task, member):
    with pytest.raises(RestrictedError):
        member.delete()


def test_str_returns_name(label):
    assert str(label) == label.name


def test_default_color_is_black(workspace):
    label = Label.objects.create(name="NoColor", workspace=workspace)
    assert label.color == "#000000"


def test_label_deleted_when_workspace_deleted(label, workspace):
    pk = label.pk
    workspace.delete()
    assert not Label.objects.filter(pk=pk).exists()


def test_label_can_be_attached_to_task(task, label):
    task.label.add(label)
    assert label in task.label.all()
    assert task in label.tasks.all()
