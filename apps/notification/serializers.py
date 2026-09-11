from rest_framework.serializers import ModelSerializer, Serializer

from notification.models import  Comments, Notification


class NotificationsModelSerializer(Serializer):
    class Meta:
        model = Notification
        fields = "__all__"


class NotificationRetrieveModelSerializer(ModelSerializer):
    class Meta:
        model = Comments
        fields = '__all__'

    def save(self):
        pk = self.context['id']
        mention = Notification.objects.filter(id=pk).first()
        mention.is_read = True
        comment = Comments.objects.filter(id=mention.comment.id).first()
        mention.save(update_fields=['is_read'])
        return comment
