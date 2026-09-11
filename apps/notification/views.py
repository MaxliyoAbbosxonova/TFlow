from drf_spectacular.utils import extend_schema
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK
from rest_framework.views import APIView

from notification.models import  Notification
from notification.serializers import NotificationsModelSerializer, \
    NotificationRetrieveModelSerializer


# Create your views here.

@extend_schema(tags=['Notifications'])
class NotificationListApiView(ListAPIView):
    serializer_class = NotificationsModelSerializer

    def get_queryset(self):
        return Notification.objects.filter(recipient=self.request.user).all()

@extend_schema(tags=['Notifications'])
class NotificationReadApiView(APIView):
    serializer_class = NotificationRetrieveModelSerializer

    def get(self, request, id):
        serializer = self.serializer_class(
            context={'id': id}
        )

        notification = serializer.save()

        return Response(
            self.serializer_class(notification).data,
            status=HTTP_200_OK
        )
