import pytest
from task.models import Task


@pytest.fixture
def task1(db, project, member):
    return Task.objects.create(
        project=project,
        assignee=member,
        reporter=member,

    )
