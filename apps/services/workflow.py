
from rest_framework.exceptions import ValidationError

from task.models import Task

ALLOWED_TRANSITIONS={
    Task.Workflow.TODO:{Task.Workflow.IN_PROGRESS,Task.Workflow.ARCHIVED},
    Task.Workflow.IN_PROGRESS:{Task.Workflow.TODO,Task.Workflow.CODE_REVIEW,Task.Workflow.ARCHIVED},
    Task.Workflow.CODE_REVIEW:{Task.Workflow.IN_PROGRESS,Task.Workflow.QA,Task.Workflow.ARCHIVED},
    Task.Workflow.QA:{Task.Workflow.CODE_REVIEW,Task.Workflow.DONE,Task.Workflow.ARCHIVED},
    Task.Workflow.DONE:{Task.Workflow.QA,Task.Workflow.ARCHIVED},
    Task.Workflow.ARCHIVED:set(),
}


def validate_status(current_status,new_status):
    if current_status == new_status:
        raise ValidationError(f"Task allaqachon '{new_status}' statusida.")

    allowed=ALLOWED_TRANSITIONS.get(current_status,set())
    if new_status not in allowed:
        raise ValidationError(
            f"'{current_status}' statusidan '{new_status}' statusiga o'tish mumkin emas. "
            f"Ruxsat etilgan: {', '.join(allowed) or 'yo`q'}"
        )

def validate_subtask_done(task):
    incomplete_children=task.get_children().exclude(status=Task.Workflow.DONE)
    if incomplete_children.exists():
        titles = ', '.join(incomplete_children.values_list('title', flat=True))
        raise ValidationError(
            f"Task'ni DONE qilib bo'lmaydi. Quyidagi subtasklar hali tugallanmagan: {titles}"
        )


