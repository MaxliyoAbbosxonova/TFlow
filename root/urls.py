"""
URL configuration for tflow project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

from root.settings import MEDIA_URL, MEDIA_ROOT
from users.views import TokenRefreshView

urlpatterns = [
                  path('admin/', admin.site.urls),
                  path('auth/', include('users.urls')),
                  path('workspaces/',include('workspace.urls')),
                  path('tasks/',include('task.urls')),
                  path('teams/',include('team.urls')),
                  path('projects/',include('project.urls')),
                  path('comments/',include('comment.urls')),
                  path('notifications/',include('notification.urls')),
                  path('audit_logs/',include('audit_log.urls')),
                  path('files/',include('shared.urls')),
                  path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
                  # Optional UI:
                  path('', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
                  path('api/schema/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
                  # path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
                  path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

              ] + static(MEDIA_URL, document_root=MEDIA_ROOT)
