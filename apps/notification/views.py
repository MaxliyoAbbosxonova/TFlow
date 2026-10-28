from drf_spectacular.utils import extend_schema
from notification.models import Notification
from notification.serializers import (
    NotificationRetrieveModelSerializer,
    NotificationsModelSerializer,
)
from rest_framework.generics import ListAPIView
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK
from rest_framework.views import APIView

# Create your views here.

@extend_schema(tags=['Notifications'])
class NotificationListApiView(ListAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = NotificationsModelSerializer
    pagination_class = LimitOffsetPagination

    def get_queryset(self):
        return Notification.objects.filter(recipient=self.request.user).all()


@extend_schema(tags=['Notifications'])
class NotificationReadApiView(APIView):
    serializer_class = NotificationRetrieveModelSerializer
    permission_classes = (IsAuthenticated,)

    def get(self, request, id):
        serializer = self.serializer_class(
            context={'id': id, 'request': request}
        )

        comment = serializer.save()

        return Response(
            self.serializer_class(comment).data,
            status=HTTP_200_OK
        )
