from django.db import transaction
from django.db.models import Q
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema
from realtime.utils import emit_to_project
from rest_framework.generics import (
    CreateAPIView,
    DestroyAPIView,
    ListAPIView,
    RetrieveUpdateDestroyAPIView,
)
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_201_CREATED
from rest_framework.views import APIView
from services.audit import create_audit_log
from services.tasks import (
    attach_label,
    change_assignee,
    change_deadline,
    change_priority,
    change_status,
    create_label,
    create_task,
    delete_task,
)
from shared.permissions import (
    IsOwnerManagerFormLabel,
    IsTeamLeadOrEmployee,
    IsTeamLeadOrManager,
    IsTeamLeadOrManagerForDeleteTask,
    LabelManagePermission,
    TasksCRUDPermission,
)
from task.models import Label, Task
from task.serializers import (
    AttachLabelSerilaizer,
    ChangeAssigneeSerializer,
    ChangeDeadLineSerializer,
    ChangePrioritySerializer,
    ChangeStatusSerializer,
    DeleteTaskSerializer,
    LabelModelSerilalizer,
    TaskAdminModelSerializer,
    TaskModelSerializer,
)
from workspace.models import Workspace, WorkspaceMember

# Create your views here.


@extend_schema(tags=["Tasks"])
class TaskListAdminApiView(ListAPIView):
    serializer_class = TaskAdminModelSerializer
    pagination_class = LimitOffsetPagination
    queryset = Task.objects.all()
    permission_classes = (IsAdminUser,)
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['project', 'assignee', 'status', 'priority', 'label',
                        'deadline', 'created_at']


@extend_schema(tags=["Tasks"])
class TaskCreateApiView(CreateAPIView):
    serializer_class = TaskModelSerializer
    queryset = Task.objects.all()
    parser_classes = [MultiPartParser, FormParser]
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        request=TaskModelSerializer,
        responses=TaskModelSerializer,
    )
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        task = create_task(serializer.validated_data, request)
        return Response(data={'task': task.id,
                              'titile': task.title,
                              'reporter': task.reporter.id,
                              'assignee': task.assignee.id,
                              'project': task.project.title}, status=HTTP_201_CREATED)


@extend_schema(tags=["Tasks"])
class TaskRetrieveUpdateDestroy(RetrieveUpdateDestroyAPIView):
    queryset = Task.objects.all()
    serializer_class = TaskModelSerializer
    permission_classes = (TasksCRUDPermission,)

    def perform_update(self, serializer):
        old_assignee = serializer.instance.assignee_id
        task = serializer.save()

        if task.assignee_id != old_assignee and task.project_id:
            emit_to_project(task.project_id, "task:assignee_changed", {
                "task_id": task.id,
                "old_assignee": old_assignee,
                "new_assignee": task.assignee_id,
                "changed_by": self.request.user.id,
            })


@extend_schema(tags=["Tasks"])
class ChangeAssignee(APIView):
    serializer_class = ChangeAssigneeSerializer
    permission_classes = (IsTeamLeadOrManager,)
    parser_classes = (MultiPartParser,)

    def patch(self, request, task_id, new_assignee):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        change_assignee(task_id, new_assignee, request.user.id)
        return Response({'detail': "Assignee o`zgartirildi."}, status=HTTP_200_OK)


@extend_schema(tags=["Tasks"])
class ChangePriority(APIView):
    serializer_class = ChangePrioritySerializer
    permission_classes = (IsTeamLeadOrManager,)

    def patch(self, request, task_id):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        change_priority(task_id, serializer.validated_data['priority'],user_id=request.user.id)
        return Response({'detail': "Priority o`zgartirildi."}, status=HTTP_200_OK)


@extend_schema(tags=["Tasks"])
class ChangeDeadLine(APIView):
    serializer_class = ChangeDeadLineSerializer
    permission_classes = (IsTeamLeadOrManager,)

    def patch(self, request, task_id):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        change_deadline(task_id, serializer.validated_data['deadline'],user_id=request.user.id)
        return Response({'detail': "Deadline o`zgartirildi."}, status=HTTP_200_OK)


@extend_schema(tags=["Tasks"])
class ChangeStatus(APIView):
    serializer_class = ChangeStatusSerializer
    permission_classes = (IsAuthenticated, IsTeamLeadOrEmployee)

    def patch(self, request, task_id):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        actor = WorkspaceMember.objects.filter(user=request.user).first()
        change_status(task_id, serializer.validated_data['status'], actor)
        return Response({'detail': "Status o`zgartirildi."}, status=HTTP_200_OK)


@extend_schema(tags=['Tasks'])
class DeleteTaskApiView(APIView):
    serializer_class = DeleteTaskSerializer
    permission_classes = (IsAuthenticated, IsTeamLeadOrManagerForDeleteTask,)

    def patch(self, request, task_id):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        delete_task(task_id,request.user.id)
        return Response({'detail': "Task o`chirildi"}, status=HTTP_200_OK)


class LabelListApiView(ListAPIView):
    serializer_class = LabelModelSerilalizer
    permission_classes = (IsAuthenticated,)
    pagination_class = LimitOffsetPagination

    def get_queryset(self):
        user = self.request.user

        print("USER:", user.id, user.email)

        print(
            "WORKSPACES:",
            list(
                Workspace.objects.filter(
                    Q(owner=user) | Q(members__user=user)
                ).distinct().values_list("id", flat=True)
            )
        )

        qs = Label.objects.filter(
            Q(workspace__owner=user) |
            Q(workspace__members__user=user)
        ).distinct()

        print(
            "LABELS:",
            list(qs.values_list("id", "name", "workspace_id"))
        )
        print(
            "OWNED:",
            list(
                Workspace.objects.filter(
                    owner=user
                ).values_list("id", flat=True)
            )
        )

        print(
            "MEMBER:",
            list(
                WorkspaceMember.objects.filter(
                    user=user
                ).values_list("workspace_id", flat=True)
            )
        )

        ws_id = self.request.query_params.get("workspace")
        return qs.filter(workspace_id=ws_id) if ws_id else qs


@extend_schema(tags=['Label'])
class LabelListCreateApiView(APIView):
    serializer_class = LabelModelSerilalizer
    pagination_class = LimitOffsetPagination
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        serializer = self.serializer_class(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        label = create_label(serializer.validated_data)
        create_audit_log(actor=WorkspaceMember.objects.filter(user=request.user.id).first(), action="CREATED LABEL",
                         model=Label.objects.filter(id=label.id).first()
                         )
        return Response(data={"detail": "Label yaratildi",
                              'id': label.id}, status=HTTP_201_CREATED)


class LabelDestroyApiView(DestroyAPIView):
    queryset = Label.objects.select_related("workspace")
    permission_classes = (IsAuthenticated, LabelManagePermission)

    def destroy(self, request, *args, **kwargs):
        label = self.get_object()  # topilmasa 404
        create_audit_log(
            actor=WorkspaceMember.objects.filter(
                user=request.user, workspace=label.workspace).first(),
            action="DELETED LABEL", model=label,
        )
        label.delete()
        return Response({"detail": "Label o'chirildi"}, status=HTTP_200_OK)


@extend_schema(tags=['Label'])
class AttachLabelToTask(APIView):
    serializer_class = AttachLabelSerilaizer
    permission_classes = (IsOwnerManagerFormLabel,)

    def post(self, request):
        with transaction.atomic():
            serializer = self.serializer_class(data=request.data)
            serializer.is_valid(raise_exception=True)
            task = attach_label(serializer.validated_data)

            return Response(data={'detail': 'Label biriktirildi',
                                  'label': LabelModelSerilalizer(task.label.all(), many=True).data}, status=HTTP_200_OK)
