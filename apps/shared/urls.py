from django.urls import path, include
from rest_framework.routers import DefaultRouter

from shared.views import FileUploadViewSet, ProjectStatisticsApiView

router = DefaultRouter()
router.register(r'', FileUploadViewSet)  # URL: /api/files/

urlpatterns = [
    path('', include(router.urls)),  # Include ViewSet URLs
    path('statistics/<int:pk>',ProjectStatisticsApiView.as_view(),)
]
