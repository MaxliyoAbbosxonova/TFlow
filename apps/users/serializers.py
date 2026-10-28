from django.db import transaction
from django.utils.text import gettext_lazy as _
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.fields import CharField, EmailField, IntegerField
from rest_framework.serializers import ModelSerializer, Serializer
from rest_framework_simplejwt.tokens import RefreshToken, TokenError

from shared.utils import check_sms_code, clear_login_key, is_verified
from users.models import Profile, Users


class UserModelSerializer(ModelSerializer):
    class Meta:
        model = Users
        fields = ('id', 'email', 'phone', 'date_joined', 'profile', 'status')


class ProfileModelSerializer(ModelSerializer):
    class Meta:
        model = Profile
        fields = "__all__"


class ProfileDataForWorkspaceMembers(ModelSerializer):
    class Meta:
        model = Profile
        fields = ('username', 'first_name', 'last_name', 'image')


class UserListForWorkspaceMembers(ModelSerializer):
    profile = ProfileDataForWorkspaceMembers()

    class Meta:
        model = Users
        fields = ('id', 'email', 'phone', 'profile', 'status')


class Register(ModelSerializer):
    token_class = RefreshToken
    profile = ProfileModelSerializer()

    class Meta:
        model = Users
        fields = ('email', 'phone', 'password', 'profile')
        write_only_fields = ('password',)

    def validate(self, attrs):
        phone = attrs['phone']

        if Users.objects.filter(phone=phone).exists():
            raise ValidationError({
                "phone": "Bu telefon raqam ro'yxatdan o'tgan"
            })

        return attrs

    def create(self, validated_data):
        with transaction.atomic():
            password = validated_data.pop('password')
            item = validated_data.pop('profile')
            user = Users(**validated_data, profile=Profile.objects.create(**item))
            user.set_password(password)

            user.save()
            return user


class LoginSerializer(Serializer):
    email = EmailField(max_length=50)
    password = CharField(write_only=True)
    token_class = RefreshToken

    def validate(self, validated_data):
        self.user = Users.objects.filter(email=validated_data['email']).first()

        if not (self.user and self.user.check_password(validated_data['password'])):
            raise ValidationError("Parol yoki email xato")

        if self.user.status == Users.Status.BLOCKED or not self.user.is_active:
            raise ValidationError("Foydalanuvchi bloklangan")

        return validated_data

    @property
    def get_data(self):
        refresh = self.get_token(self.user)
        return {
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "user": UserModelSerializer(self.user).data}

    @classmethod
    def get_token(cls, user):
        return cls.token_class.for_user(user)


class RefreshTokenSerializer(serializers.Serializer):
    refresh = serializers.CharField()

    default_error_messages = {
        'bad_token': _('Token is invalid or expired')
    }

    def validate(self, attrs):
        self.token = attrs['refresh']
        return attrs

    def save(self, **kwargs):
        try:
            RefreshToken(self.token).blacklist()
        except TokenError:
            self.fail('bad_token')


class PasswordResetSerializer(Serializer):
    email = EmailField()
    new_pass = CharField(write_only=True)
    token_class = RefreshToken

    def validate(self, validated_data):
        email = validated_data['email']
        self.user = Users.objects.filter(email=email).first()
        if not self.user:
            raise ValidationError("Bunday foydalanuvchi mavjud emas")
        validated_data['user'] = self.user
        if not is_verified(email=email):
            raise ValidationError("Tasdiqlanmadi !")

        return validated_data

    def save(self):
        email = self.validated_data['email']
        password = self.validated_data['new_pass']
        user = Users.objects.filter(email=email).first()
        user.set_password(password)
        user.save(update_fields=['password'])
        clear_login_key(email)

        return user

    @property
    def get_data(self):
        refresh = self.get_token(self.user)
        return {
            "access": str(refresh.access_token),
            "refresh": str(refresh)
        }

    @classmethod
    def get_token(cls, user):
        return cls.token_class.for_user(user)


class SendSmsCodeSerializer(ModelSerializer):
    email = EmailField()

    class Meta:
        model = Users
        fields = ['email']


class CheckSmsCodeSerializer(Serializer):
    email = EmailField()
    code = IntegerField()

    def validate(self, validated_data):
        email = validated_data.get('email')
        code = validated_data.get('code')

        if not check_sms_code(email, code):
            raise ValidationError('Invalid code')

        self.user = Users.objects.filter(email=validated_data['email']).first()
        if not self.user:
            raise ValidationError('Code entered correct but user is not registered ')
        return validated_data


class ChangeUserStatusSerializer(ModelSerializer):
    class Meta:
        model = Users
        fields = ("id", 'status')

    def validate(self, attrs):
        request = self.context["request"]
        if self.instance.pk == request.user.pk and attrs.get("status") == Users.Status.BLOCKED:
            raise ValidationError("O'zingizni bloklay olmaysiz.")
        return attrs
