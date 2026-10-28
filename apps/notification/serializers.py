from notification.models import Notification
from rest_framework.exceptions import NotFound
from rest_framework.serializers import ModelSerializer


class NotificationsModelSerializer(ModelSerializer):
    class Meta:
        model = Notification
        fields = "__all__"


class NotificationRetrieveModelSerializer(ModelSerializer):
    class Meta:
        model = Notification
        fields = '__all__'

    def save(self):
        pk = self.context['id']
        notification = Notification.objects.select_related('comment').filter(id=pk, recipient=self.context[
            'request'].user).first()
        if notification is None:
            raise NotFound("Notification topilmadi")

        if not notification.is_read:
            notification.is_read = True
            notification.save(update_fields=['is_read', 'read_at'])
        if notification.comment:
            return notification.comment
        else:
            return notification
