from django.contrib import admin
from django.contrib.admin import ModelAdmin
from task.models import Label, Task

# Register your models here.


@admin.register(Task)
class TaskAdmin(ModelAdmin):
    list_display = ('id', 'title','project', 'assignee', 'reporter', 'deadline', 'status')
    list_display_links = ('id', 'title', 'assignee', 'reporter')


@admin.register(Label)
class LabelAdmin(ModelAdmin):
    list_display = ('id', 'name', 'color')
    list_display_links = ('id', 'name', 'color')
