from rest_framework.exceptions import ValidationError
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

    def validate(self, attrs):
        # PATCH/PUT da qiymatlar attrs da bo'lmasligi mumkin, shuning uchun instance dan olamiz
        parent = attrs.get("parent", getattr(self.instance, "parent", None))
        project = attrs.get("project", getattr(self.instance, "project", None))

        if parent and project and parent.project_id != project.id:
            raise ValidationError(
                {"parent": "Subtask parent taskning projectidan tashqarida bo'lishi mumkin emas."}
            )
        return attrs

class ChangeAssigneeSerializer(Serializer):
    pass


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

    def validate(self, validated_data):
        name = validated_data['name']
        color = validated_data['color']
        workspace = validated_data['workspace']

        if Label.objects.filter(name=name, color=color, workspace=workspace).exists():
            raise ValidationError("Label alla qachon qo'shilgan")
        return validated_data


class LabelDestroySerilalizer(ModelSerializer):
    class Meta:
        model = Label
        fields = '__all__'

    def validate(self, validated_data):
        pk = validated_data['pk']
        instance = Label.objects.filter(id=pk).first()
        if not instance:
            raise ValidationError('Bunday label mavjud emas')


class AttachLabelSerilaizer(Serializer):
    task = IntegerField(required=True)
    label = IntegerField(required=True)

    def validate(self, validated_data):
        task_id = validated_data['task']
        label_id = validated_data['label']
        task = Task.objects.filter(id=task_id).first()
        label = Label.objects.filter(id=label_id).first()
        if task.project.workspace != label.workspace:
            raise ValidationError("Label va Task bir workspace dan emas")
        if Task.objects.filter(id=task_id, label=label_id).exists():
            raise ValidationError("Label taskga alla qachon biriktirilgan ")

        return validated_data
