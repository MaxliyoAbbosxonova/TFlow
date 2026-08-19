from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.db.models import CharField, Model, ImageField, CASCADE, OneToOneField
from django.db.models.fields import DateTimeField, EmailField, TextField
from django.utils import timezone


# Create your models here.
class UserManager(BaseUserManager):

    def create_user(self, email, phone, password=None, **extra_fields):
        if not email:
            raise ValueError("Email kiritilishi kerak")

        if not phone:
            raise ValueError("Telefon raqam kiritilishi kerak")

        email = self.normalize_email(email)

        user = self.model(
            email=email,
            phone=phone,
            **extra_fields
        )

        user.set_password(password)
        user.save(using=self._db)

        return user

    def create_superuser(self, email, phone, password=None, **extra_fields):

        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault(
            "role",
            Users.Role.ADMIN
        )

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser is_staff=True bo'lishi kerak")

        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser is_superuser=True bo'lishi kerak")

        return self.create_user(
            email=email,
            phone=phone,
            password=password,
            **extra_fields
        )


class Profile(Model):
    username = CharField(max_length=20)
    first_name = CharField(max_length=50, null=False)
    last_name = CharField(max_length=50, null=False)
    birth = DateTimeField(null=True)

    image = ImageField(
        upload_to="profiles/",
        null=True,
        blank=True
    )
    bio = TextField(
        blank=True,
        default=""
    )

    created_at = DateTimeField(
        auto_now_add=True
    )

    updated_at = DateTimeField(
        auto_now=True
    )

    def __str__(self):
        return self.username


class Users(AbstractUser):
    username = None
    email = EmailField(max_length=50, unique=True, null=False)
    profile = OneToOneField(Profile, on_delete=CASCADE, null=True, related_name='user')
    phone = CharField(max_length=14, default=901234567)
    date_joined = DateTimeField(default=timezone.now)
    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["phone"]

    def __str__(self):
        return self.email
