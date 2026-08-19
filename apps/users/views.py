from django.db.migrations import serializer
from drf_spectacular.utils import extend_schema
from rest_framework import permissions, status
from rest_framework.generics import GenericAPIView
from rest_framework.generics import ListAPIView, ListCreateAPIView
from rest_framework.permissions import IsAdminUser, AllowAny
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK
from rest_framework.views import APIView
from rest_framework_simplejwt.settings import api_settings
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenViewBase

from users.models import Users, Profile
from users.serializers import UserModelSerializer, Register, ProfileModelSerializer, LoginSerializer, \
    RefreshTokenSerializer, PasswordResetSerializer


# Create your views here.

@extend_schema(tags=['User'])
class UsersListApiView(ListAPIView):
    queryset = Users.objects.all()
    serializer_class = UserModelSerializer
    permission_classes = [IsAdminUser, ]


@extend_schema(tags=['User'])
class RegisterApiView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    serializer_class = Register

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        refresh = RefreshToken.for_user(user)

        return Response({
            "access": str(refresh.access_token),
            "refresh": str(refresh)
        })


@extend_schema(tags=['Profile'])
class ProfileListApiView(ListCreateAPIView):
    serializer_class = ProfileModelSerializer

    def get_queryset(self):
        if self.request.user.is_superuser:
            return Profile.objects.all()


@extend_schema(tags=['Profile'])
class ProfileListUpdateApiView(APIView):
    serializer_class = ProfileModelSerializer
    permission_classes = (AllowAny,)

    def get(self, request):
        profile = request.user.profile

        serializer = self.serializer_class(profile)

        return Response(serializer.data)

    def patch(self, request):
        profile = request.user.profile

        serializer = self.serializer_class(
            profile,
            data=request.data,
            partial=True
        )

        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data)


@extend_schema(tags=['User'])
class LoginApiView(APIView):
    serializer_class = LoginSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)

        return Response(serializer.get_data)


@extend_schema(tags=['User'])
class TokenRefreshView(TokenViewBase):
    """
    Takes a refresh type JSON web token and returns an access type JSON web
    token if the refresh token is valid.
    """

    _serializer_class = api_settings.TOKEN_REFRESH_SERIALIZER


token_refresh = TokenRefreshView.as_view()


class LogoutView(GenericAPIView):
    serializer_class = RefreshTokenSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, *args):
        sz = self.get_serializer(data=request.data)
        sz.is_valid(raise_exception=True)
        sz.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

class Password_Reset(APIView):
    serializer_class=PasswordResetSerializer
    permission_classes = (AllowAny,)

    def post(self,request):
        serializer=self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data,status=HTTP_200_OK)