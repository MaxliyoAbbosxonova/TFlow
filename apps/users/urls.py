from django.urls import path
from users.views import UsersListApiView, RegisterApiView, ProfileListApiView, ProfileListUpdateApiView, LoginApiView, \
    LogoutView, Password_Reset
from django.urls import path

from users.views import UsersListApiView, RegisterApiView, ProfileListApiView, ProfileListUpdateApiView, LoginApiView, \
    LogoutView, Password_Reset

urlpatterns = [
    path('', UsersListApiView.as_view()),
    path('register/', RegisterApiView.as_view()),
    path('profiles/', ProfileListApiView.as_view()),
    path('me/', ProfileListUpdateApiView.as_view()),
    path('login/', LoginApiView.as_view()),
    path('logout/', LogoutView.as_view()),
    (path('p_reset/', Password_Reset.as_view()))
]
