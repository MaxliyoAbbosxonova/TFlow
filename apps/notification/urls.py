from django.urls import path
from notification.views import NotificationListApiView, NotificationReadApiView

urlpatterns = [
    path('', NotificationListApiView.as_view(), name="notifications-list"),  # list notifications(my)
    path('<int:id>/', NotificationReadApiView.as_view(), name="notifications-read"),  # read notification

]
