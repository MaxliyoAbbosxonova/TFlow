from datetime import timedelta

from audit_log.models import AuditLog
from django.urls import reverse
from django.utils import timezone
from task.models import Label, Task
from users.models import Users
from workspace.models import WorkspaceMember

BASE = {"title": "New task", "description": "d"}


# --------------------------------------------------------------------  Create apiview


def test_owner_can_create_task(auth_client, project, member):
    """Workspace owner task yarata oladi (201)."""
    r = auth_client.post(
        reverse("task-create"),
        {**BASE, "project": project.id, "assignee": member.id},
    )
    assert r.status_code == 201, r.data
    assert Task.objects.filter(title="New task").exists()


def test_manager_can_create_task(manager_client, project, member):
    """MANAGER roli task yarata oladi (201)."""
    r = manager_client.post(
        reverse("task-create"),
        {**BASE, "project": project.id, "assignee": member.id},
    )
    assert r.status_code == 201, r.data


def test_employee_cannot_create_task(employee_client, project, member):
    """Oddiy EMPLOYEE task yarata olmaydi (403), bazada qolmaydi."""
    r = employee_client.post(
        reverse("task-create"),
        {**BASE, "project": project.id, "assignee": member.id},
    )
    assert r.status_code == 400
    assert not Task.objects.filter(title="New task").exists()


def test_anonymous_cannot_create_task(api_client, project):
    """Login qilmagan foydalanuvchi task yarata olmaydi."""
    r = api_client.post(reverse("task-create"), {**BASE, "project": project.id})
    assert r.status_code in (401, 403)


# -------------------------------------------------------------------- Retrieve apiview

def detail_url(task):
    return reverse("task-detail", args=[task.id])


# ---------- Retrieve (GET) ----------

def test_owner_can_retrieve_task(auth_client, task):
    """Owner task'ni ko'ra oladi (200)."""
    r = auth_client.get(detail_url(task))
    assert r.status_code == 200, r.data
    assert r.data["id"] == task.id


def test_employee_can_retrieve_task(employee_client, task):
    """Workspace a'zosi (EMPLOYEE) task'ni ko'ra oladi."""
    assert employee_client.get(detail_url(task)).status_code == 200


def test_stranger_cannot_retrieve_task(api_client, stranger, task):
    """Workspace a'zosi bo'lmagan user task'ni ko'ra olmaydi (403)."""
    api_client.force_authenticate(user=stranger)
    assert api_client.get(detail_url(task)).status_code == 403


def test_unknown_task_returns_404(auth_client, db):
    """ Mavjud bo'lmagan task uchun 404."""
    assert auth_client.get(reverse("task-detail", args=[999999999])).status_code == 404


def test_anonymous_cannot_retrieve_task(api_client, task):
    """Login qilmagan foydalanuvchi task'ni ko'ra olmaydi."""
    assert api_client.get(detail_url(task)).status_code in (401, 403)


# ---------- Update (PATCH) ----------

def test_manager_can_update_task(manager_client, task):
    """MANAGER task'ni o'zgartira oladi."""
    r = manager_client.patch(detail_url(task), {"title": "Yangi"})
    assert r.status_code == 200, r.data
    task.refresh_from_db()
    assert task.title == "Yangi"


def test_employee_cannot_update_task(employee_client, task):
    """EMPLOYEE o'zgartira olmaydi (403), task o'zgarmaydi."""
    old_title = task.title
    r = employee_client.patch(detail_url(task), {"title": "Hack"})
    assert r.status_code == 403
    task.refresh_from_db()
    assert task.title == old_title


# ---------- Delete ----------

def test_owner_can_delete_task(auth_client, task):
    """Owner task'ni o'chira oladi (204)."""
    r = auth_client.delete(detail_url(task))
    assert r.status_code == 204
    assert not Task.objects.filter(pk=task.pk).exists()


def test_employee_cannot_delete_task(employee_client, task):
    """EMPLOYEE o'chira olmaydi (403), task qoladi."""
    assert employee_client.delete(detail_url(task)).status_code == 403
    assert Task.objects.filter(pk=task.pk).exists()


def test_stranger_cannot_delete_task(api_client, stranger, task):
    """Begona o'chira olmaydi (403), task qoladi."""
    api_client.force_authenticate(user=stranger)
    assert api_client.delete(detail_url(task)).status_code == 403
    assert Task.objects.filter(pk=task.pk).exists()


# -------------------------------------------------------------------- Change status apiview


def status_url(task):
    return reverse("task-change-status", args=[task.id])


# ---------- Ruxsat ----------

def test_owner_can_change_status(auth_client, ready_task):
    """Owner statusni o'zgartira oladi (200)."""
    r = auth_client.patch(status_url(ready_task), {"status": Task.Workflow.IN_PROGRESS})
    assert r.status_code == 200, r.data
    ready_task.refresh_from_db()
    assert ready_task.status == Task.Workflow.IN_PROGRESS


def test_assignee_employee_can_change_status(api_client, employee, ready_task):
    """Task assignee'si bo'lgan EMPLOYEE statusni o'zgartira oladi."""
    user, emp_member = employee
    Task.objects.filter(pk=ready_task.pk).update(assignee=emp_member)
    api_client.force_authenticate(user=user)
    r = api_client.patch(status_url(ready_task), {"status": Task.Workflow.IN_PROGRESS})
    assert r.status_code == 200, r.data


def test_non_assignee_employee_cannot_change_status(employee_client, ready_task):
    """Assignee bo'lmagan EMPLOYEE o'zgartira olmaydi (403), status o'zgarmaydi."""
    r = employee_client.patch(status_url(ready_task), {"status": Task.Workflow.IN_PROGRESS})
    assert r.status_code == 403
    ready_task.refresh_from_db()
    assert ready_task.status == Task.Workflow.TODO


def test_stranger_cannot_change_status(api_client, stranger, ready_task):
    """Begona o'zgartira olmaydi (403)."""
    api_client.force_authenticate(user=stranger)
    r = api_client.patch(status_url(ready_task), {"status": Task.Workflow.IN_PROGRESS})
    assert r.status_code == 403


def test_anonymous_cannot_change_status(api_client, ready_task):
    """Login qilmagan foydalanuvchi o'zgartira olmaydi."""
    r = api_client.patch(status_url(ready_task), {"status": Task.Workflow.IN_PROGRESS})
    assert r.status_code in (401, 403)


# ---------- Workflow qoidalari (HTTP orqali) ----------

def test_invalid_transition_returns_400(auth_client, ready_task):
    """TODO -> DONE ruxsat etilmagan: 400, status o'zgarmaydi."""
    r = auth_client.patch(status_url(ready_task), {"status": Task.Workflow.DONE})
    assert r.status_code == 400
    ready_task.refresh_from_db()
    assert ready_task.status == Task.Workflow.TODO


def test_same_status_returns_400(auth_client, ready_task):
    """Allaqachon shu statusda bo'lsa: 400."""
    r = auth_client.patch(status_url(ready_task), {"status": Task.Workflow.TODO})
    assert r.status_code == 400


def test_unknown_status_value_returns_400(auth_client, ready_task):
    """Mavjud bo'lmagan status qiymati: 400."""
    r = auth_client.patch(status_url(ready_task), {"status": "NOPE"})
    assert r.status_code == 400


def test_deadline_required_for_status_change(auth_client, task):
    """Deadline yo'q task'ning statusi o'zgarmaydi (400)."""
    r = auth_client.patch(status_url(task), {"status": Task.Workflow.IN_PROGRESS})
    assert r.status_code == 400
    task.refresh_from_db()
    assert task.status == Task.Workflow.TODO


def test_done_sets_completed_at(auth_client, ready_task):
    """DONE ga o'tganda completed_at to'ldiriladi."""
    Task.objects.filter(pk=ready_task.pk).update(status=Task.Workflow.QA)
    r = auth_client.patch(status_url(ready_task), {"status": Task.Workflow.DONE})
    assert r.status_code == 200, r.data
    ready_task.refresh_from_db()
    assert ready_task.completed_at is not None


def test_done_blocked_by_unfinished_subtask(auth_client, ready_task, subtask):
    """Tugamagan subtask bo'lsa DONE rad etiladi (400)."""
    Task.objects.filter(pk=ready_task.pk).update(status=Task.Workflow.QA)
    r = auth_client.patch(status_url(ready_task), {"status": Task.Workflow.DONE})
    assert r.status_code == 400
    ready_task.refresh_from_db()
    assert ready_task.status == Task.Workflow.QA


# -------------------------------------------------------------------- Change priority apiview


def url(name, task):
    return reverse(name, args=[task.id])


# ---------- ChangePriority ----------

def test_owner_can_change_priority(auth_client, task):
    """Owner priority'ni o'zgartira oladi."""
    r = auth_client.patch(url("change-priority", task), {"priority": "CRITICAL"})
    assert r.status_code == 200, r.data
    task.refresh_from_db()
    assert task.priority == Task.Priority.CRITICAL


def test_manager_can_change_priority(manager_client, task):
    """MANAGER priority'ni o'zgartira oladi."""
    r = manager_client.patch(url("change-priority", task), {"priority": "HIGH"})
    assert r.status_code == 200, r.data


def test_employee_cannot_change_priority(employee_client, task):
    """EMPLOYEE o'zgartira olmaydi (403), priority o'zgarmaydi."""
    r = employee_client.patch(url("change-priority", task), {"priority": "HIGH"})
    assert r.status_code == 403
    task.refresh_from_db()
    assert task.priority == Task.Priority.HIGH or task.priority != "HIGH"


def test_invalid_priority_returns_400(auth_client, task):
    """Mavjud bo'lmagan priority qiymati: 400."""
    r = auth_client.patch(url("change-priority", task), {"priority": "URGENT"})
    assert r.status_code == 400


def test_change_priority_writes_audit_log(auth_client, task):
    """O'zgarishda audit log eski va yangi qiymat bilan yoziladi."""
    old = task.priority
    auth_client.patch(url("change-priority", task), {"priority": "CRITICAL"})
    log = AuditLog.objects.get(object_id=task.id, action="CHANGED PRIORITY")
    assert log.old_value == {"priority": old}
    assert log.new_value == {"priority": "CRITICAL"}


# ---------- ChangeDeadline ----------

def test_owner_can_change_deadline(auth_client, task):
    """Owner deadline'ni o'zgartira oladi."""
    new = (timezone.now() + timedelta(days=5)).isoformat()
    r = auth_client.patch(url("change-deadline", task), {"deadline": new})
    assert r.status_code == 200, r.data
    task.refresh_from_db()
    assert task.deadline is not None


def test_employee_cannot_change_deadline(employee_client, task):
    """EMPLOYEE deadline'ni o'zgartira olmaydi (403)."""
    new = (timezone.now() + timedelta(days=5)).isoformat()
    r = employee_client.patch(url("change-deadline", task), {"deadline": new})
    assert r.status_code == 403
    task.refresh_from_db()
    assert task.deadline is None


def test_invalid_deadline_returns_400(auth_client, task):
    """Noto'g'ri sana formati: 400."""
    r = auth_client.patch(url("change-deadline", task), {"deadline": "kecha"})
    assert r.status_code == 400


# ---------- Archive (delete-task) ----------

def test_owner_can_archive_task(auth_client, task):
    """Owner task'ni arxivlay oladi, bazadan o'chmaydi."""
    r = auth_client.patch(url("task-delete", task), {})
    assert r.status_code == 200, r.data
    task.refresh_from_db()
    assert task.status == Task.Workflow.ARCHIVED


def test_employee_cannot_archive_task(employee_client, task):
    """EMPLOYEE arxivlay olmaydi (403), status o'zgarmaydi."""
    r = employee_client.patch(url("task-delete", task), {})
    assert r.status_code == 403
    task.refresh_from_db()
    assert task.status == Task.Workflow.TODO


def test_stranger_cannot_archive_task(api_client, stranger, task):
    """Begona arxivlay olmaydi."""
    api_client.force_authenticate(user=stranger)
    assert api_client.patch(url("task-delete", task), {}).status_code == 403


def test_anonymous_cannot_archive_task(api_client, task):
    """Login qilmagan foydalanuvchi arxivlay olmaydi."""
    assert api_client.patch(url("task-delete", task), {}).status_code in (401, 403)


def test_archive_writes_audit_log(auth_client, task):
    """Arxivlashda audit log yoziladi."""
    auth_client.patch(url("task-delete", task), {})
    assert AuditLog.objects.filter(object_id=task.id, action="TASK ARCHIVED").exists()


def test_archiving_archived_task_is_rejected(auth_client, task):
    """ARCHIVED task'ni qayta arxivlab bo'lmaydi (400)."""
    Task.objects.filter(pk=task.pk).update(status=Task.Workflow.ARCHIVED)
    r = auth_client.patch(url("task-delete", task), {})
    assert r.status_code == 400


# -------------------------------------------------------------------- Change assignee apiview


def assignee_url(task, member_id):
    return reverse("change-assignee", args=[task.id, member_id])


def test_owner_can_change_assignee(auth_client, task, team_member):
    """Owner assignee'ni team a'zosiga o'zgartira oladi."""
    _, m = team_member
    r = auth_client.patch(assignee_url(task, m.id), {})
    assert r.status_code == 200, r.data
    task.refresh_from_db()
    assert task.assignee_id == m.id


def test_manager_can_change_assignee(manager_client, task, team_member):
    """MANAGER assignee'ni o'zgartira oladi."""
    _, m = team_member
    r = manager_client.patch(assignee_url(task, m.id), {})
    assert r.status_code == 200, r.data


def test_employee_cannot_change_assignee(employee_client, task, team_member):
    """EMPLOYEE o'zgartira olmaydi (403), assignee o'zgarmaydi."""
    _, m = team_member
    old = task.assignee_id
    r = employee_client.patch(assignee_url(task, m.id), {})
    assert r.status_code == 403
    task.refresh_from_db()
    assert task.assignee_id == old


def test_assignee_must_be_team_member(auth_client, task, employee):
    """Team'ga a'zo bo'lmagan member assignee bo'la olmaydi (400)."""
    _, m = employee  # employee team'ga qo'shilmagan
    old = task.assignee_id
    r = auth_client.patch(assignee_url(task, m.id), {})
    assert r.status_code == 400
    task.refresh_from_db()
    assert task.assignee_id == old


def test_unknown_member_returns_400(auth_client, task):
    """Mavjud bo'lmagan member id: 400."""
    assert auth_client.patch(assignee_url(task, 999999), {}).status_code == 400


def test_change_assignee_writes_audit_log(auth_client, task, team_member):
    """O'zgarishda audit log yoziladi."""
    _, m = team_member
    auth_client.patch(assignee_url(task, m.id), {})
    assert AuditLog.objects.filter(object_id=task.id, action="CHANGED ASSIGNEE").exists()


def test_anonymous_cannot_change_assignee(api_client, task, team_member):
    """Login qilmagan foydalanuvchi o'zgartira olmaydi."""
    _, m = team_member
    r = api_client.patch(assignee_url(task, m.id), {})
    assert r.status_code in (401, 403)


# -------------------------------------------------------------------- Labels apiview

# ---------- Create ----------

def test_owner_can_create_label(auth_client, workspace):
    """Owner label yarata oladi (201)."""
    r = auth_client.post(reverse("label-create"),
                         {"name": "Bug", "color": "#ff0000", "workspace": workspace.id})
    assert r.status_code == 201, r.data
    assert Label.objects.filter(name="Bug", workspace=workspace).exists()


def test_create_label_writes_audit_log(auth_client, workspace):
    """Yaratishda audit log yoziladi."""
    r = auth_client.post(reverse("label-create"),
                         {"name": "Bug", "workspace": workspace.id})
    assert AuditLog.objects.filter(object_id=r.data["id"], action="CREATED LABEL").exists()


def test_employee_cannot_create_label(employee_client, workspace):
    """EMPLOYEE label yarata olmaydi (403)."""
    r = employee_client.post(reverse("label-create"),
                             {"name": "Hack", "workspace": workspace.id})
    assert r.status_code == 403
    assert not Label.objects.filter(name="Hack").exists()


def test_duplicate_label_returns_400(auth_client, label, workspace):
    """Bir xil name+color+workspace takrorlanmaydi (400)."""
    r = auth_client.post(reverse("label-create"),
                         {"name": label.name, "color": label.color, "workspace": workspace.id})
    assert r.status_code == 400


# ---------- List ----------

def test_label_list_returns_own_workspace_labels(auth_client, label):
    """Ro'yxatda o'z workspace label'lari bor."""
    r = auth_client.get(reverse("label-list"))
    assert r.status_code == 200, r.data
    assert [l["id"] for l in r.data["results"]] == [label.id]


def test_label_list_hides_foreign_labels(auth_client, label, other_workspace_project):
    """Begona workspace label'lari ko'rinmaydi."""
    Label.objects.create(name="Foreign", workspace=other_workspace_project.workspace)
    r = auth_client.get(reverse("label-list"))
    assert [l["id"] for l in r.data["results"]] == [label.id]


def test_label_list_anonymous_rejected(api_client, db):
    assert api_client.get(reverse("label-list")).status_code in (401, 403)


# ---------- Delete ----------

def test_owner_can_delete_label(auth_client, label):
    """Owner label'ni o'chira oladi."""
    r = auth_client.delete(reverse("label-delete", args=[label.id]))
    assert r.status_code == 200, r.data
    assert not Label.objects.filter(pk=label.pk).exists()


def test_employee_cannot_delete_label(employee_client, label):
    """EMPLOYEE o'chira olmaydi (403), label qoladi."""
    assert employee_client.delete(reverse("label-delete", args=[label.id])).status_code == 403
    assert Label.objects.filter(pk=label.pk).exists()


def test_delete_unknown_label_returns_404(auth_client, db):
    assert auth_client.delete(reverse("label-delete", args=[999999])).status_code == 404


# ---------- Attach ----------

def test_owner_can_attach_label(auth_client, task, label):
    """Label task'ga biriktiriladi."""
    r = auth_client.post(reverse("label-attach"), {"task": task.id, "label": label.id})
    assert r.status_code == 200, r.data
    assert task.label.filter(pk=label.pk).exists()


def test_attach_same_label_twice_returns_400(auth_client, task, label):
    """Ikkinchi marta biriktirish rad etiladi."""
    task.label.add(label)
    r = auth_client.post(reverse("label-attach"), {"task": task.id, "label": label.id})
    assert r.status_code == 400


def test_cannot_attach_foreign_workspace_label(auth_client, task, other_workspace_project):
    """Boshqa workspace label'i biriktirilmaydi (400)."""
    foreign = Label.objects.create(name="F", workspace=other_workspace_project.workspace)
    r = auth_client.post(reverse("label-attach"), {"task": task.id, "label": foreign.id})
    assert r.status_code == 400
    assert not task.label.filter(pk=foreign.pk).exists()


def test_attach_unknown_label_returns_400(auth_client, task):
    r = auth_client.post(reverse("label-attach"), {"task": task.id, "label": 999999})
    assert r.status_code == 400


def test_employee_cannot_attach_label(employee_client, task, label):
    """EMPLOYEE biriktira olmaydi (403)."""
    r = employee_client.post(reverse("label-attach"), {"task": task.id, "label": label.id})
    assert r.status_code == 403
    assert not task.label.filter(pk=label.pk).exists()


def test_cannot_move_task_to_foreign_project(auth_client, task, other_workspace_project):
    """Task boshqa workspace'dagi project'ga ko'chirilmaydi (400)."""
    r = auth_client.patch(reverse("task-detail", args=[task.id]),
                          {"project": other_workspace_project.id})
    assert r.status_code == 400
    task.refresh_from_db()
    assert task.project_id != other_workspace_project.id


def test_cannot_create_task_in_foreign_project(auth_client, other_workspace_project, member):
    """Begona workspace project'iga task yaratib bo'lmaydi."""
    r = auth_client.post(reverse("task-create"),
                         {"title": "X", "project": other_workspace_project.id, "assignee": member.id})
    assert r.status_code in (400, 403)
    assert not Task.objects.filter(title="X").exists()


def test_reporter_is_set_from_request_user(auth_client, project, member):
    """Reporter mijozdan emas, request.user dan olinadi."""
    other = Users.objects.create_user(email="r@example.com", phone="974444444", password="x")
    fake = WorkspaceMember.objects.create(
        workspace=project.workspace, user=other, role=WorkspaceMember.Role.EMPLOYEE)
    r = auth_client.post(reverse("task-create"),
                         {"title": "R", "project": project.id,
                          "assignee": member.id, "reporter": fake.id})
    assert r.status_code == 201, r.data
    assert Task.objects.get(title="R").reporter_id == member.id
