from django.urls import path, include
from rest_framework.routers import DefaultRouter

from shared.views import MultipleFileUploadView, FileUploadViewSet

router = DefaultRouter()
router.register(r'', FileUploadViewSet)  # URL: /api/files/

urlpatterns = [
    path('upload/', MultipleFileUploadView.as_view(), name='multiple-file-upload'),  # URL: /api/upload/
    path('', include(router.urls)),  # Include ViewSet URLs
]
