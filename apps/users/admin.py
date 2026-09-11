from django.contrib import admin
from django.contrib.admin import ModelAdmin
from django.contrib.auth.admin import UserAdmin
from django.utils.safestring import mark_safe

from users.models import Users, Profile


# Register your models here.

@admin.register(Users)
class UsersAdmin(UserAdmin):
    ordering = ('email',)
    list_display_links = ('email',)

    list_display = (
        'id',
        'email',
        'phone',
        'profile',
        'is_active',)

    search_fields = (
        'email',
        'phone',
        'profile__username',
        'profile__first_name',
        'profile__last_name',
    )

    list_filter = (

        'is_active',
        'is_staff',
        'is_superuser',
    )

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal info", {"fields": ("profile", "phone")}),
        (
            "Permissions",
            {
                "fields": ("is_active",
                           "is_staff",
                           "is_superuser",
                           "groups",
                           "user_permissions",
                           ),
            },
        ),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("usable_password", "password1", "password2"),
            },
        ),
    )


@admin.register(Profile)
class Profile(ModelAdmin):
    list_display = ('username', 'first_name', 'last_name', 'birth', 'created_at', 'image_tag')
    list_display_links =( 'username','image_tag')
    def image_tag(self, obj):
        if obj.image:
            return mark_safe(
                f'<img src="{obj.image.url}" width="90" height="90" style="object-fit: cover;" />'
            )
        return "—"
