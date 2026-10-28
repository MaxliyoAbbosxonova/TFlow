from comment.models import Comments
from rest_framework.exceptions import ValidationError
from rest_framework.serializers import ModelSerializer
from workspace.models import WorkspaceMember


class CommentsModelSerializer(ModelSerializer):
    class Meta:
        model = Comments
        fields = "__all__"


class CommentCreateModelSerializer(ModelSerializer):
    class Meta:
        model = Comments
        fields = ("task", "text")

    def validate_task(self, task):
        user = self.context["request"].user
        ws = task.project.workspace
        is_member = WorkspaceMember.objects.filter(user=user, workspace=ws).exists()
        if not is_member and ws.owner_id != user.id:
            raise ValidationError("Siz bu workspace a'zosi emassiz")
        return task


class ReplyCommentSerializer(ModelSerializer):
    class Meta:
        model = Comments
        fields = ("task", "text", "parent")

    def validate(self, attrs):
        parent = attrs.get("parent")
        if parent and parent.task_id != attrs["task"].id:
            raise ValidationError("Reply parent komment bilan bir xil taskda bo'lishi kerak.")
        return attrs
