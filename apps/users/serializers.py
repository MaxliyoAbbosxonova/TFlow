import re

from django.utils.text import gettext_lazy as _
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.fields import EmailField, CharField, IntegerField
from rest_framework.serializers import Serializer, ModelSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.tokens import TokenError

from shared.utils import check_sms_code
from users.models import Users, Profile


class UserModelSerializer(ModelSerializer):
    class Meta:
        model = Users
        fields = ('id', 'email', 'phone', 'date_joined', 'profile','status')


class ProfileModelSerializer(ModelSerializer):
    class Meta:
        model = Profile
        fields = "__all__"


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
        password = validated_data.pop('password')
        item = validated_data.pop('profile')
        user = Users(**validated_data, profile=Profile.objects.create(**item))
        user.set_password(password)

        user.save()
        return user


class LoginSerializer(Serializer):
    email = EmailField(max_length=50)
    password = CharField(max_length=8)
    token_class = RefreshToken

    def validate(self, validated_data):
        self.user = Users.objects.filter(email=validated_data['email']).first()

        if not self.user:
            raise ValidationError("Parol yoki email xato")
        if not self.user.check_password(validated_data['password']):
            raise ValidationError("Parol yoki email xato")

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
    old_pass = CharField(max_length=8)
    new_pass = CharField(max_length=8)

    def validate(self, validated_data):
        self.user = Users.objects.filter(email=validated_data['email']).first()

        if not self.user.check_password(validated_data['old_pass']):
            raise ValidationError("Parolni unuttingizmi")
        if not self.user:
            raise ValidationError("Bunday foydalanuvchi mavjud emas")
        if validated_data["old_pass"] == validated_data['new_pass']:
            raise ValidationError("Yangi parol eskisidan farq qilishi kerak")

        validated_data['user'] = self.user

        return validated_data

    def save(self):
        user = self.validated_data['user']
        new = self.validated_data['new_pass']
        user.set_password(new)
        user.save(update_fields=['password'])

        return user


class SendSmsCodeSerializer(ModelSerializer):
    email = EmailField()

    class Meta:
        model = Users
        fields = ['email']

class CheckSmsCodeSerializer(Serializer):
    email = EmailField()
    code = IntegerField()
    password=CharField()
    token_class = RefreshToken


    def validate(self, validated_data):
        email = validated_data.get('email')
        code = validated_data.get('code')

        if not check_sms_code(email, code):
            raise ValidationError('Invalid code')

        self.user = Users.objects.filter(email=validated_data['email']).first()
        if not self.user:
            raise ValidationError('Code entered correct but user is not registered ')
        return validated_data

    def save(self):
        email = self.validated_data['email']
        password = self.validated_data['password']
        user=Users.objects.filter(email=email).first()
        user.set_password(password)
        user.save(update_fields=['password'])

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


class ChangeUserStatusSerializer(ModelSerializer):
    class Meta:
        model=Users
        fields=("id",'status')
