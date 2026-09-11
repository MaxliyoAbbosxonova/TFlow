from django.db import transaction
from rest_framework.exceptions import NotFound, ValidationError

from services.audit import create_audit_log
from services.workflow import validate_status, validate_subtask_done
from task.models import Task
from task.tasks import send_assignee_notification_task, send_status_notification_task
from workspace.models import WorkspaceMember


def get_task_or_404(task_id):
    task = Task.objects.filter(id=task_id).first()
    if not task:
        raise NotFound('Task not found')
    return task


def format_member(member):
    return f"ID-{member.user.id} -- {member.user.profile.first_name} {member.user.profile.last_name}"


@transaction.atomic
def create_task(validated_data):
    task=Task.objects.create(**validated_data)
    create_audit_log(actor=task.reporter, action='CREATE',
                     model=task,
                     new_value={
                         "title": task.title,
                         "priority": task.priority,
                         "deadline": str(task.deadline) if task.deadline else None,
                     })
    send_assignee_notification_task(task)
    return task



@transaction.atomic
def change_assignee(task_id, new_assignee):
    member = WorkspaceMember.objects.filter(id=new_assignee).first()
    task = get_task_or_404(task_id)
    if not member:
        raise ValidationError('Task not found')

    create_audit_log(
        actor=task.reporter,
        action='CHANGED ASSIGNEE',
        model=task,
        old_value={"assignee": format_member(task.assignee)},
        new_value={"assignee": format_member(member)},
    )
    task.assignee = member
    task.save(update_fields=['assignee'])
    send_assignee_notification_task(task)
    return task


@transaction.atomic
def change_priority(task_id, priority):
    task = get_task_or_404(task_id)
    old_priority = task.priority
    new_priority = priority

    create_audit_log(
        actor=task.reporter,
        action='CHANGED PRIORITY',
        model=task,
        old_value={"priority": old_priority},
        new_value={"priority": new_priority},
    )
    task.priority = new_priority
    task.save(update_fields=['priority'])
    return task


@transaction.atomic
def change_deadline(task_id, deadline):
    task = get_task_or_404(task_id)
    old_deadline = task.deadline
    new_deadline = deadline
    task.deadline = deadline

    create_audit_log(
        actor=task.reporter,
        action='CHANGED DEADLINE',
        model=task,
        old_value={"deadline": old_deadline},
        new_value={"deadline": new_deadline},
    )
    task.deadline = deadline
    task.save(update_fields=['deadline'])
    return task


@transaction.atomic
def change_status(task_id, status):
    task = get_task_or_404(task_id)
    old_status = task.status
    new_status = status

    validate_status(current_status=task.status, new_status=status)
    if new_status == Task.Workflow.DONE:
        validate_subtask_done(task=task)

    action = 'TASK ARCHIVED' if new_status == Task.Workflow.ARCHIVED else 'CHANGED STATUS'

    create_audit_log(
        actor=task.reporter,
        action=action,
        model=task,
        old_value={"status": old_status},
        new_value={"status": new_status},
    )
    task.status = new_status
    task.save(update_fields=['status'])
    send_status_notification_task(task)
    return task


@transaction.atomic
def delete_task(task_id):
    task = get_task_or_404(task_id)
    old_status = task.status
    new_status = Task.Workflow.ARCHIVED
    action = 'TASK ARCHIVED'

    create_audit_log(
        actor=task.reporter,
        action=action,
        model=task,
        old_value={"status": old_status},
        new_value={"status": new_status},
    )
    task.status = new_status
    task.save(update_fields=['status'])
    return task
