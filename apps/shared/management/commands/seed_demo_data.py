"""
Create a connected demo dataset for the project models.

Run from the Django project root:
    python manage.py seed_demo_data

This command is intended for a development/test database. It does not delete
existing data. Use a fresh database to avoid unique-name/email conflicts.
"""
from datetime import timedelta

from django.apps import apps
from django.contrib.contenttypes.models import ContentType
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone


def model_named(name):
    """Find a model by class name without hard-coding its Django app label."""
    matches = [model for model in apps.get_models() if model.__name__ == name]
    if len(matches) != 1:
        labels = [model._meta.label for model in matches]
        raise RuntimeError(
            f"Expected exactly one model named {name}; found {labels}. "
            "Update model_named() if your project has duplicate model names."
        )
    return matches[0]


class Command(BaseCommand):
    help = "Create connected demo data for users, workspaces, projects and tasks."

    @transaction.atomic
    def handle(self, *args, **options):
        Users = model_named("Users")
        Profile = model_named("Profile")
        Workspace = model_named("Workspace")
        WorkspaceMember = model_named("WorkspaceMember")
        Team = model_named("Team")
        Project = model_named("Project")
        Task = model_named("Task")
        Label = model_named("Label")
        Comments = model_named("Comments")
        Notification = model_named("Notification")
        WorkspaceInvitation = model_named("WorkspaceInvitation")
        FileUpload = model_named("FileUpload")
        AuditLog = model_named("AuditLog")

        now = timezone.now()

        # 10 profiles + 10 users. Passwords are hashed by create_user().
        profiles = []
        users = []
        for i in range(1, 11):
            profile = Profile.objects.create(
                username=f"demo_user_{i}",
                first_name=["Ali", "Malika", "Jasur", "Madina", "Aziz",
                            "Dilnoza", "Sardor", "Sevara", "Bekzod", "Nodira"][i - 1],
                last_name=["Karimov", "Usmonova", "Rahimov", "Tursunova",
                           "Ismoilov", "Qodirova", "Ergashev", "Saidova",
                           "Yuldashev", "Nazarova"][i - 1],
                birth=now - timedelta(days=8000 + i * 120),
                bio=f"Demo profile {i} for development and testing.",
            )
            user = Users.objects.create_user(
                email=f"demo.user{i}@example.com",
                phone=f"+998900000{i:02d}",
                password="DemoPass123!",
                first_name=profile.first_name,
                last_name=profile.last_name,
                profile=profile,
                is_active=True,
                status=Users.Status.ACTIVE,
            )
            profiles.append(profile)
            users.append(user)

        # 5 workspaces, each owned by an existing user.
        workspaces = []
        for i in range(1, 6):
            workspaces.append(Workspace.objects.create(
                name=f"Demo Workspace {i}",
                description=f"Development workspace number {i}.",
                owner=users[i - 1],
            ))

        # 10 members; every role is represented and all memberships have a
        # valid workspace. Two members are assigned to each workspace.
        role_cycle = [
            WorkspaceMember.Role.WORKSPACE_OWNER,
            WorkspaceMember.Role.ADMIN,
            WorkspaceMember.Role.MANAGER,
            WorkspaceMember.Role.TEAM_LEAD,
            WorkspaceMember.Role.EMPLOYEE,
            WorkspaceMember.Role.EMPLOYEE,
            WorkspaceMember.Role.MANAGER,
            WorkspaceMember.Role.TEAM_LEAD,
            WorkspaceMember.Role.ADMIN,
            WorkspaceMember.Role.EMPLOYEE,
        ]
        members = []
        for i in range(10):
            workspace = workspaces[i // 2]
            members.append(WorkspaceMember.objects.create(
                workspace=workspace,
                user=users[i],
                role=role_cycle[i],
            ))

        # 10 teams; each team's lead belongs to the same workspace.
        teams = []
        for i in range(10):
            workspace = workspaces[i // 2]
            lead_member = members[i // 2]
            teams.append(Team.objects.create(
                name=f"Demo Team {i + 1}",
                workspace=workspace,
                team_lead=lead_member.user,
            ))
        # Keep M2M team memberships inside the same workspace.
        for i, member in enumerate(members):
            member.team.add(teams[(i // 2) * 2], teams[(i // 2) * 2 + 1])

        # 10 projects; each project's team, workspace and member agree.
        projects = []
        project_statuses = [
            Project.Status.ACTIVE, Project.Status.PLANNED,
            Project.Status.ACTIVE, Project.Status.COMPLETED,
            Project.Status.PLANNED, Project.Status.ACTIVE,
            Project.Status.ARCHIVED, Project.Status.ACTIVE,
            Project.Status.PLANNED, Project.Status.COMPLETED,
        ]
        for i in range(10):
            workspace_index = i // 2
            team = teams[i]
            member = members[workspace_index * 2 + (i % 2)]
            projects.append(Project.objects.create(
                title=f"Demo Project {i + 1}",
                team=team,
                workspace=workspaces[workspace_index],
                member=member,
                status=project_statuses[i],
                description=f"Demo project {i + 1}; all linked records use its workspace.",
                deadline=now + timedelta(days=30 + i),
            ))

        # 10 labels, each attached to one of the 5 workspaces.
        labels = []
        label_colors = ["#2563EB", "#16A34A", "#DC2626", "#9333EA", "#EA580C",
                        "#0891B2", "#CA8A04", "#DB2777", "#4F46E5", "#0F766E"]
        for i in range(10):
            labels.append(Label.objects.create(
                name=f"Demo Label {i + 1}",
                color=label_colors[i],
                workspace=workspaces[i // 2],
            ))

        # 10 uploaded-file records with real in-memory file content.
        # These create files under the configured MEDIA_ROOT.
        file_uploads = []
        for i in range(1, 11):
            upload = FileUpload()
            upload.file.save(
                f"demo_attachment_{i}.txt",
                ContentFile(f"Demo attachment {i}\n".encode("utf-8")),
                save=True,
            )
            file_uploads.append(upload)

        # 20 tasks: 10 root tasks + 10 subtasks. Each subtask uses the same
        # project as its parent, satisfying Task.clean().
        tasks = []
        for i in range(10):
            project = projects[i]
            workspace_index = i // 2
            reporter = members[workspace_index * 2]
            assignee = members[workspace_index * 2 + 1]
            root = Task.objects.create(
                title=f"Main task {i + 1}",
                description=f"Main task {i + 1} for {project.title}.",
                project=project,
                parent=None,
                reporter=reporter,
                assignee=assignee,
                priority=[
                    Task.Priority.LOW, Task.Priority.MEDIUM, Task.Priority.HIGH,
                    Task.Priority.CRITICAL,
                ][i % 4],
                status=Task.Workflow.IN_PROGRESS if i % 2 == 0 else Task.Workflow.TODO,
                deadline=now + timedelta(days=10 + i),
                file=file_uploads[i],
            )
            root.label.add(labels[workspace_index * 2], labels[workspace_index * 2 + 1])
            tasks.append(root)

            subtask = Task.objects.create(
                title=f"Subtask {i + 1}",
                description=f"Subtask {i + 1} belonging to {root.title}.",
                project=project,
                parent=root,
                reporter=reporter,
                assignee=assignee,
                priority=Task.Priority.MEDIUM,
                status=Task.Workflow.DONE if i % 3 == 0 else Task.Workflow.TODO,
                deadline=now + timedelta(days=5 + i),
                completed_at=now - timedelta(days=1) if i % 3 == 0 else None,
                file=file_uploads[10 - i - 1],
            )
            subtask.label.add(labels[workspace_index * 2])
            tasks.append(subtask)

        # 10 comments. Authors and tasks are valid; a few comments reply to
        # an earlier comment on the same task.
        comments = []
        for i in range(10):
            task = tasks[i * 2]  # one of the root tasks
            # Two comments share each root task; the second can reply to the first.
            task = tasks[(i // 2) * 2]
            comment = Comments.objects.create(
                author=users[i],
                task=task,
                text=f"Demo comment {i + 1}: progress update for {task.title}.",
                parent=comments[i - 1] if i % 2 == 1 else None,
            )
            comments.append(comment)

        # 10 notifications; every recipient exists and optional task/comment
        # references are valid.
        notification_types = [
            Notification.NotificationType.TASK_ASSIGNED,
            Notification.NotificationType.MENTION,
            Notification.NotificationType.STATUS_CHANGED,
            Notification.NotificationType.DEADLINE_SOON,
            Notification.NotificationType.TASK_OVERDUE,
            Notification.NotificationType.WORKSPACE_INVITATION,
        ]
        for i in range(10):
            is_read = i % 3 == 0
            Notification.objects.create(
                recipient=users[i],
                notification_type=notification_types[i % len(notification_types)],
                title=f"Demo notification {i + 1}",
                message=f"Notification {i + 1} related to {tasks[i].title}.",
                task=comments[i].task,
                comment=comments[i],
                is_read=is_read,
                read_at=now - timedelta(hours=i + 1) if is_read else None,
            )

        # 10 invitations; inviter is a member of the invited workspace.
        invitation_statuses = [
            WorkspaceInvitation.Status.PENDING,
            WorkspaceInvitation.Status.ACCEPTED,
            WorkspaceInvitation.Status.EXPIRED,
            WorkspaceInvitation.Status.REVOKED,
        ]
        for i in range(10):
            workspace_index = i // 2
            WorkspaceInvitation.objects.create(
                workspace=workspaces[workspace_index],
                email=f"invitee{i + 1}@example.com",
                invited_by=members[workspace_index * 2],
                role=role_cycle[(i + 1) % len(role_cycle)],
                status=invitation_statuses[i % len(invitation_statuses)],
                expires_at=now + timedelta(days=7) if i % 4 == 0 else now - timedelta(days=1),
            )

        # 10 generic audit logs referencing existing Task rows.
        task_content_type = ContentType.objects.get_for_model(Task)
        for i in range(10):
            AuditLog.objects.create(
                actor=members[(i // 2) * 2],
                action=f"DEMO_TASK_UPDATED_{i + 1}",
                content_type=task_content_type,
                object_id=tasks[i * 2].pk,
                old_value={"status": Task.Workflow.TODO},
                new_value={"status": tasks[i].status},
            )

        self.stdout.write(self.style.SUCCESS(
            "Demo data created: 10 users, 10 profiles, 5 workspaces, "
            "10 workspace members, 10 teams, 10 projects, 20 tasks "
            "(10 parent tasks + 10 subtasks), 10 labels, 10 comments, "
            "10 notifications, 10 invitations, 10 file uploads and 10 audit logs."
        ))
