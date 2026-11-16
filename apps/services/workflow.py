from django.core.exceptions import ObjectDoesNotExist
from rest_framework.exceptions import ValidationError
from task.models import Task, WorkflowStatus, WorkflowTransition



def validate_status(current_status, new_status,project):
    if current_status == new_status:
        raise ValidationError(f"Task allaqachon '{new_status}' statusida.")

    try:
        workflow=project.workflow
    except ObjectDoesNotExist:
        raise ValidationError("Bu loyihada workflow sozlanmagan:")
    if new_status.workflow.id!=workflow.id:
        raise ValidationError("Bu status shu loyihaga tegishli emas.")

    allowed=WorkflowTransition.objects.filter(workflow=project.workflow,from_status=current_status,to_status=new_status).exists()
    if  not  allowed:
        raise ValidationError(
            f"'{current_status}' statusidan '{new_status.name}' statusiga o'tish mumkin emas. "
        )

def validate_subtask_done(task):
    incomplete_children = task.get_children().exclude(status__category=WorkflowStatus.Category.DONE)
    if incomplete_children.exists():
        titles = ', '.join(incomplete_children.values_list('title', flat=True))
        raise ValidationError(
            f"Task'ni DONE qilib bo'lmaydi. Quyidagi subtasklar hali tugallanmagan: {titles}"
        )
