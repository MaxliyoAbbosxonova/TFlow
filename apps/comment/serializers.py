from rest_framework.serializers import ModelSerializer, Serializer

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

    def create(self, validated_data):
        request = self.context['request']
        comments = Comments.objects.create(author=request.user, **validated_data)
        return comments


import re


class CommentCreateModelSerializer(ModelSerializer):
    class Meta:
        model = Comments
        fields = ("task", "text")

    def create(self, validated_data):
        request = self.context['request']
        author_profile = Profile.objects.filter(user=request.user).first()
        comment = Comments.objects.create(author=request.user, **validated_data)
        task = validated_data["task"]
        text = validated_data["text"]
        actor=WorkspaceMember.objects.filter(user=request.user).first()

        mentions = set(re.findall(r"@([a-zA-Z0-9_]+)", text))
        create_audit_log(actor=actor,
                         action="COMMENT TO TASK",
                         model=comment,
                         )
        for username in mentions:
            profile = Profile.objects.filter(username=username).first()

            if not profile:
                continue
            send_notification(recipient=profile.user,
                              notification_type=Notification.NotificationType.MENTION,
                              comment=comment,
                              task=task,
                              message=text,
                              title=f"@{author_profile.username} Mentioned you on comment"
                              )

        return comment


class ReplyCommentSerializer(ModelSerializer):
    class Meta:
        model=Comments
        fields=("task", "text",'parent')
        
    def create(self, validated_data):
        request = self.context['request']
        author_profile = Profile.objects.filter(user=request.user).first()
        comment = Comments.objects.create(author=request.user, **validated_data)
        task = validated_data["task"]
        text = validated_data["text"]
        actor=WorkspaceMember.objects.filter(user=request.user).first()

        mentions = set(re.findall(r"@([a-zA-Z0-9_]+)", text))
        create_audit_log(actor=actor,
                         action="COMMENT TO TASK",
                         model=comment,
                         )
        for username in mentions:
            profile = Profile.objects.filter(username=username).first()

            if not profile:
                continue
            send_notification(recipient=profile.user,
                              notification_type=Notification.NotificationType.MENTION,
                              comment=comment,
                              task=task,
                              message=text,
                              title=f"@{author_profile.username} Mentioned you on comment"
                              )

        return comment

