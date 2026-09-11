from django.urls import path

from notification.views import NotificationListApiView, NotificationReadApiView

urlpatterns = [
    path('', NotificationListApiView.as_view()),  # list notifications(my)
    path('<int:id>/', NotificationReadApiView.as_view()),  # read notification

]
