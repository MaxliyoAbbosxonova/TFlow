from rest_framework.fields import IntegerField, ChoiceField, DateTimeField
from rest_framework.serializers import ModelSerializer, ListSerializer, Serializer

from shared.utils import RecursiveField
from task.models import Task, Label


class TaskAdminModelSerializer(ModelSerializer):
    children = ListSerializer(child=RecursiveField(), source='get_children', read_only=True)

    class Meta:
        model = Task
        fields = "__all__"


class TaskModelSerializer(ModelSerializer):
    children = ListSerializer(child=RecursiveField(), source='get_children', read_only=True)

    class Meta:
        model = Task
        fields = ("id", 'project', "title", 'description', "assignee", "reporter", "deadline", "priority", "children",
                  'parent', 'file')


class ChangeAssigneeSerializer(Serializer):
    task_id = TaskModelSerializer()
    new_assignee = IntegerField()


class ChangePrioritySerializer(Serializer):
    priority = ChoiceField(choices=Task.Priority.choices)


class ChangeDeadLineSerializer(Serializer):
    deadline = DateTimeField()


class ChangeStatusSerializer(Serializer):
    status = ChoiceField(choices=Task.Workflow.choices)


class DeleteTaskSerializer(Serializer):
    pass


class LabelModelSerilalizer(ModelSerializer):
    class Meta:
        model = Label
        fields = '__all__'


class AttachLabelSerilaizer(Serializer):
    task = IntegerField(required=True)
    label = IntegerField(required=True)

    def save(self):
        task_id = self.validated_data['task']
        label_id = self.validated_data['label']

        task = Task.objects.filter(id=task_id).first()
        label = Label.objects.filter(id=label_id).first()
        task.label = label
        task.save(updated_fiels=['label'])

        return task
