from project.models import Project
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.fields import ChoiceField, DateTimeField, IntegerField
from rest_framework.serializers import ListSerializer, ModelSerializer, Serializer
from shared.utils import RecursiveField
from task.models import Label, Task
from workspace.models import WorkspaceMember


class TaskAdminModelSerializer(ModelSerializer):
    children = ListSerializer(child=RecursiveField(), source='get_children', read_only=True)

    class Meta:
        model = Task
        fields = "__all__"


class TaskModelSerializer(ModelSerializer):
    children = ListSerializer(child=RecursiveField(), source='get_children', read_only=True)

    class Meta:
        model = Task
        fields = ("id", 'project', "title", 'description', "assignee", "deadline", "priority", "children",
                  'parent', 'file')

    def validate(self, attrs):
        parent = attrs.get("parent", getattr(self.instance, "parent", None))
        project = attrs.get("project", getattr(self.instance, "project", None))

        if parent and project and parent.project_id != project.id:
            raise ValidationError(
                {"parent": "Subtask parent taskning projectidan tashqarida bo'lishi mumkin emas."}
            )

        if project and project.status == Project.Status.ARCHIVED:
            raise ValidationError("ARCHIVED project uchun task yaratib bo'lmaydi.")

        return attrs

    def validate_project(self, project):
        if self.instance and project != self.instance.project:
            raise ValidationError("Task'ni boshqa project'ga ko'chirib bo'lmaydi.")
        return project


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

    def validate_workspace(self, ws):
        request = self.context.get("request")
        if request is not None:
            user = request.user
            allowed = (
                    user.is_staff
                    or ws.owner_id == user.id
                    or ws.members.filter(user=user, role=WorkspaceMember.Role.MANAGER).exists()
            )
            if not allowed:
                raise PermissionDenied("Bu workspace'da label yarata olmaysiz.")
        return ws

    def validate_project(self, project):
        if self.instance and project != self.instance.project:
            raise ValidationError("Task'ni boshqa project'ga ko'chirib bo'lmaydi.")
        return project

    def validate(self, attrs):
        if Label.objects.filter(name=attrs['name'], color=attrs.get('color', '#000000'),
                                workspace=attrs['workspace']).exists():
            raise ValidationError("Label allaqachon qo'shilgan")
        return attrs


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
        if not label:
            raise ValidationError('bad request')
        if task.project.workspace != label.workspace:
            raise ValidationError("Label va Task bir workspace dan emas")
        if Task.objects.filter(id=task_id, label=label_id).exists():
            raise ValidationError("Label taskga alla qachon biriktirilgan ")

        return validated_data
