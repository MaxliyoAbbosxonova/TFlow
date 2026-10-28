from concurrent.futures import ThreadPoolExecutor

import pytest
from audit_log.models import AuditLog
from django.db import connection
from rest_framework.exceptions import ValidationError
from services.tasks import change_status
from task.models import Task


def run_two_attempts(task, member):
    def attempt(_):
        try:
            change_status(task.id, Task.Workflow.IN_PROGRESS, member)
            return "ok"
        except ValidationError:
            return "rejected"
        finally:
            connection.close()

    with ThreadPoolExecutor(max_workers=2) as pool:
        return list(pool.map(attempt, range(2)))


@pytest.mark.django_db(transaction=True)
def test_concurrent_same_transition_only_one_wins(ready_task, member):
    """Bir vaqtda ikkita bir xil o'tish: faqat bittasi o'tadi."""
    results = run_two_attempts(ready_task, member)
    assert sorted(results) == ["ok", "rejected"]


@pytest.mark.django_db(transaction=True)
def test_concurrent_status_change_writes_one_audit_log(ready_task, member):
    """Parallel so'rovlarda audit logga faqat bitta yozuv tushadi."""
    run_two_attempts(ready_task, member)
    count = AuditLog.objects.filter(
        object_id=ready_task.id, action="CHANGED STATUS").count()
    assert count == 1