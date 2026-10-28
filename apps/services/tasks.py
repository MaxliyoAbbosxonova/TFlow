from django.db import transaction
from django.utils import timezone
from realtime.utils import emit_to_project
from rest_framework import status
from rest_framework.exceptions import NotFound, ValidationError
from services.audit import create_audit_log
from services.workflow import validate_status, validate_subtask_done
from task.models import Label, Task
from task.tasks import send_assignee_notification_task, send_status_notification_task
from workspace.models import WorkspaceMember


def get_task_or_404(task_id, for_update=False):
    qs = Task.objects.select_for_update() if for_update else Task.objects
    task = qs.filter(id=task_id).first()
    if not task:
        raise NotFound('Task not found')
    return task


def format_member(member):
    if member is None:
        return None
    user = member.user
    profile = getattr(user, "profile", None)
    if profile is None:
        return f"ID-{user.id} -- {user.email}"
    return f"ID-{user.id} -- {profile.first_name} {profile.last_name}"


@transaction.atomic
def create_task(validated_data, request):
    member = WorkspaceMember.objects.filter(user=request.user, workspace=validated_data['project'].workspace)
    if not member.exists():
        raise ValidationError("You can't create task on other workspace project", code=status.HTTP_400_BAD_REQUEST)

    task = Task.objects.create(reporter=member.first(), **validated_data)
    if not (task.project.workspace.members.filter(user=request.user,
                                                  role=WorkspaceMember.Role.MANAGER).exists() or task.project.team.team_lead == request.user):
        raise ValidationError('You don`t have permissions for this action')

    create_audit_log(actor=task.reporter, action='CREATE',
                     model=task,
                     new_value={
                         "title": task.title,
                         "priority": task.priority,
                         "deadline": str(task.deadline) if task.deadline else None,
                     })
    # rollback bo'lsa notification yuborilmasligi uchun
    transaction.on_commit(lambda: send_assignee_notification_task.delay(task.id))

    return task


@transaction.atomic
def change_assignee(task_id, new_assignee, changed_by: None):
    task = get_task_or_404(task_id, for_update=True)
    member = WorkspaceMember.objects.filter(id=new_assignee, team=task.project.team).first()
    actor=WorkspaceMember.objects.filter(id=changed_by).first()
    if not member:
        raise ValidationError('assignee  is  not member')

    old_assignee_id = task.assignee_id

    create_audit_log(
        actor=actor,
        action='CHANGED ASSIGNEE',

        model=task,
        old_value={"assignee": format_member(task.assignee)},
        new_value={"assignee": format_member(member)},
    )
    task.assignee = member
    task.save(update_fields=['assignee'])
    # rollback bo'lsa notification yuborilmasligi uchun
    transaction.on_commit(lambda: send_assignee_notification_task.delay(task.id))
    if task.project_id:
        emit_to_project(task.project_id, "task:assignee_changed", {
            "task_id": task.id,
            "old_assignee": old_assignee_id,  # WorkspaceMember id
            "new_assignee": member.id,  # WorkspaceMember id
            "changed_by": changed_by,  # User id
        })
    return task


@transaction.atomic
def change_priority(task_id, priority,user_id):
    task = get_task_or_404(task_id, for_update=True)
    old_priority = task.priority
    new_priority = priority
    actor=WorkspaceMember.objects.filter(id=user_id).first()

    create_audit_log(
        actor=actor,
        action='CHANGED PRIORITY',
        model=task,
        old_value={"priority": old_priority},
        new_value={"priority": new_priority},
    )
    task.priority = new_priority
    task.save(update_fields=['priority'])
    return task


@transaction.atomic
def change_deadline(task_id, deadline,user_id):
    task = get_task_or_404(task_id, for_update=True)
    old_deadline = task.deadline
    new_deadline = deadline
    task.deadline = deadline
    actor=WorkspaceMember.objects.filter(id=user_id).first()


    create_audit_log(
        actor=actor,
        action='CHANGED DEADLINE',
        model=task,
        old_value={"deadline": old_deadline.isoformat() if old_deadline else None},
        new_value={"deadline": new_deadline.isoformat()},
    )
    task.deadline = new_deadline
    task.save(update_fields=['deadline'])
    return task


@transaction.atomic
def change_status(task_id, status, actor):
    task = get_task_or_404(task_id, for_update=True)
    old_status = task.status
    new_status = status


    validate_status(current_status=old_status, new_status=new_status)
    if not (task.deadline and task.assignee):
        raise ValidationError("Deadline va Assignee majburiy maydonlar")
    if new_status == Task.Workflow.DONE:
        validate_subtask_done(task=task)

    task.status = new_status
    if new_status == Task.Workflow.DONE:
        if task.completed_at is None:
            task.completed_at = timezone.now()
    elif new_status != Task.Workflow.ARCHIVED:
        task.completed_at = None

    task.save(update_fields=['status', 'completed_at'])

    action = 'TASK ARCHIVED' if new_status == Task.Workflow.ARCHIVED else 'CHANGED STATUS'
    create_audit_log(
        actor=actor,
        action=action,
        model=task,
        old_value={"status": old_status},
        new_value={"status": new_status},
    )

    # rollback bo'lsa notification yuborilmasligi uchun
    transaction.on_commit(lambda: send_status_notification_task.delay(task.id))
    if task.project_id:
        emit_to_project(task.project_id, "task:status_changed", {
            "task_id": task.id,
            "old_status": old_status,
            "new_status": new_status,
            "changed_by": actor.user_id if actor else None,
        })
    return task


@transaction.atomic
def delete_task(task_id,user_id):
    task = get_task_or_404(task_id, for_update=True)
    old_status = task.status
    new_status = Task.Workflow.ARCHIVED
    action = 'TASK ARCHIVED'
    actor=WorkspaceMember.objects.filter(id=user_id).first()
    if old_status == Task.Workflow.ARCHIVED:
        raise ValidationError('Task already archived !', code=status.HTTP_400_BAD_REQUEST)
    create_audit_log(
        actor=actor,
        action=action,
        model=task,
        old_value={"status": old_status},
        new_value={"status": new_status},
    )
    task.status = new_status
    task.save(update_fields=['status', 'completed_at'])
    return task


@transaction.atomic
def attach_label(validated_data):
    task_id = validated_data['task']
    label_id = validated_data['label']

    task = Task.objects.filter(id=task_id).first()
    label = Label.objects.filter(id=label_id).first()
    task.label.add(label)

    return task


@transaction.atomic
def create_label(validated_data):
    label = Label.objects.create(**validated_data)
    return label
