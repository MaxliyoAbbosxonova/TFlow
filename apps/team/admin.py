from django.contrib import admin
from django.contrib.admin import ModelAdmin

from team.models import Team


# Register your models here.

@admin.register(Team)
class TeamAdmin(ModelAdmin):
    list_display = ('id', 'name')
    list_display_links = ('id', 'name')

