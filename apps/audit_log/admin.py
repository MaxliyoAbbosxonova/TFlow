from django.contrib import admin
from django.contrib.admin import ModelAdmin

from audit_log.models import AuditLog


# Register your models here.



@admin.register(AuditLog)
class AuditLogAdmin(ModelAdmin):
    list_display = ('id','action','content_type','object_id','old_value','new_value')
    list_display_links = ('id','action','old_value','new_value')