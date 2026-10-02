import re

from rest_framework.serializers import ModelSerializer

from comment.models import Comments
from notification.models import Notification
from services.audit import create_audit_log
from services.notification import send_notification
from users.models import Profile
from workspace.models import WorkspaceMember


class CommentsModelSerializer(ModelSerializer):
    class Meta:
        model = Comments
        fields = "__all__"


class CommentCreateModelSerializer(ModelSerializer):
    class Meta:
        model = Comments
        fields = ("task", "text")


class ReplyCommentSerializer(ModelSerializer):
    class Meta:
        model = Comments
        fields = ("task", "text", 'parent')

