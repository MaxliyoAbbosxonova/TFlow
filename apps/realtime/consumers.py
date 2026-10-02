from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer


class ProjectConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        user = self.scope["user"]

        # 1) Authentication
        if not user.is_authenticated:
            await self.close(code=4401)
            return

        self.project_id = self.scope["url_route"]["kwargs"]["project_id"]

        # 2) Authorization
        if not await self.has_access(user.id, self.project_id):
            await self.close(code=4403)
            return

        # 3) Faqat shundan keyin guruhga qo'shib, qabul qilamiz
        self.group_name = f"project_{self.project_id}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, code):
        if hasattr(self, "group_name"):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    # receive_json ATAYLAB yo'q: client guruhga xabar yubora olmaydi.
    # Eventlarni faqat server (view) yuboradi.

    async def project_event(self, event):
        await self.send_json(event["data"])

    @database_sync_to_async
    def has_access(self, user_id, project_id):
        from project.models import Project  # yo'lni moslang
        from workspace.models import WorkspaceMember  # yo'lni moslang

        project = (
            Project.objects
            .select_related("workspace", "member", "team")
            .filter(id=project_id)
            .first()
        )
        if project is None:
            return False

        # Workspace owner
        if project.workspace and project.workspace.owner_id == user_id:
            return True

        # Workspace ADMIN / WORKSPACE_OWNER / MANAGER
        if project.workspace_id and WorkspaceMember.objects.filter(
                user_id=user_id,
                workspace_id=project.workspace_id,
                role__in=[
                    WorkspaceMember.Role.ADMIN,
                    WorkspaceMember.Role.WORKSPACE_OWNER,
                    WorkspaceMember.Role.MANAGER,
                ],
        ).exists():
            return True

        # Project'ga to'g'ridan-to'g'ri biriktirilgan member
        if project.member_id and project.member.user_id == user_id:
            return True

        if project.team_id:
            # Team lead
            if project.team.team_lead_id == user_id:
                return True
            # Team a'zosi
            if WorkspaceMember.objects.filter(
                    user_id=user_id, team=project.team_id
            ).exists():
                return True

        return False
