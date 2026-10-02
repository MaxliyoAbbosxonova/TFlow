from django.urls import path

from users.views import SendCodeApiView, CheckCodeApiView, ChangeUserStatusAPIView
from users.views import UsersListApiView, RegisterApiView, ProfileListApiView, ProfileListUpdateApiView, LoginApiView, \
    LogoutView, PasswordReset

urlpatterns = [
    path('', UsersListApiView.as_view(), name='auth-list'),
    path('register/', RegisterApiView.as_view(),name='auth-register'),
    path('profiles/', ProfileListApiView.as_view(),name='auth-p_list'),
    path('my_profile/', ProfileListUpdateApiView.as_view(),name='auth-p_crud'),
    path('login/', LoginApiView.as_view(),name='auth-login'),
    path('logout/', LogoutView.as_view(),name='auth-logout'),
    path('password_reset/', PasswordReset.as_view(),name='auth-p_reset'),
    path('send_code/', SendCodeApiView.as_view(),name='auth-send_code'),
    path('check_code/', CheckCodeApiView.as_view(),name='auth-check_code'),
    path('change_status/<int:pk>', ChangeUserStatusAPIView.as_view(),name='auth-status'),

]
