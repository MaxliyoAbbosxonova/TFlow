from django.db import transaction
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema
from mptt.models import MPTTModel
from rest_framework.generics import RetrieveUpdateDestroyAPIView, CreateAPIView, ListAPIView, DestroyAPIView
from rest_framework.pagination import LimitOffsetPagination
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_201_CREATED
from rest_framework.views import APIView

from realtime.utils import emit_to_project
from services.audit import create_audit_log
from services.tasks import change_status, change_assignee, change_priority, change_deadline, delete_task, create_task, \
    attach_label, create_label
from shared.permissions import Tasks_CRUD_Permission, Projects_Tasks_Members, IsOwnerManagerAdmin, IsTeamLeadOrEmployee, \
    IsTeamLeadOrManager, IsOwnerManagerFormLabel
from task.models import Task, Label
from task.serializers import TaskModelSerializer, TaskAdminModelSerializer, \
    ChangeAssigneeSerializer, ChangePrioritySerializer, ChangeDeadLineSerializer, \
    ChangeStatusSerializer, DeleteTaskSerializer, LabelModelSerilalizer, AttachLabelSerilaizer, LabelDestroySerilalizer
from workspace.models import WorkspaceMember


# Create your views here.


@extend_schema(tags=["Tasks"])
class TaskListAdminApiView(ListAPIView):
    serializer_class = TaskAdminModelSerializer
    pagination_class=LimitOffsetPagination
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
    permission_classes = (Projects_Tasks_Members,)

    @extend_schema(
        request=TaskModelSerializer,
        responses=TaskModelSerializer,
    )
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        task = create_task(serializer.validated_data)
        return Response(data={'task': task.id,
                              'titile': task.title,
                              'reporter': task.reporter.id,
                              'assignee': task.assignee.id,
                              'project': task.project.title}, status=HTTP_201_CREATED)


@extend_schema(tags=["Tasks"])
class TaskRetrieveUpdateDestroy(RetrieveUpdateDestroyAPIView):
    queryset = Task.objects.all()
    serializer_class = TaskModelSerializer
    permission_classes = (Tasks_CRUD_Permission,)

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
        change_assignee(task_id, new_assignee,request.user.id)
        return Response({'detail': "Assignee o`zgartirildi."}, status=HTTP_200_OK)


@extend_schema(tags=["Tasks"])
class ChangePriority(APIView):
    serializer_class = ChangePrioritySerializer
    permission_classes = (IsTeamLeadOrManager,)


    def patch(self, request, task_id):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        change_priority(task_id, serializer.validated_data['priority'])
        return Response({'detail': "Priority o`zgartirildi."}, status=HTTP_200_OK)


@extend_schema(tags=["Tasks"])
class ChangeDeadLine(APIView):
    serializer_class = ChangeDeadLineSerializer
    permission_classes = (IsTeamLeadOrManager,)

    def patch(self, request, task_id):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        change_deadline(task_id, serializer.validated_data['deadline'])
        return Response({'detail': "Deadline o`zgartirildi."}, status=HTTP_200_OK)


@extend_schema(tags=["Tasks"])
class ChangeStatus(APIView):
    serializer_class = ChangeStatusSerializer
    permission_classes = (IsTeamLeadOrEmployee,)

    def patch(self, request, task_id):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        actor = WorkspaceMember.objects.filter(user=request.user).first()
        change_status(task_id, serializer.validated_data['status'],actor)
        return Response({'detail': "Status o`zgartirildi."}, status=HTTP_200_OK)


@extend_schema(tags=['Tasks'])
class DeleteTaskApiView(APIView):
    serializer_class = DeleteTaskSerializer
    permission_classes = (IsTeamLeadOrEmployee,)

    def patch(self, request, task_id):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        delete_task(task_id)
        return Response({'detail': "Task o`chirildi"}, status=HTTP_200_OK)


@extend_schema(tags=['Label'])
class LabelListApiView(ListAPIView):
    serializer_class = LabelModelSerilalizer
    queryset = Label.objects.all()
    permission_classes = (IsOwnerManagerFormLabel,)
    pagination_class=LimitOffsetPagination




@extend_schema(tags=['Label'])
class LabelListCreateApiView(APIView):
    serializer_class = LabelModelSerilalizer
    permission_classes = (IsTeamLeadOrManager,)
    pagination_class=LimitOffsetPagination



    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        label = create_label(serializer.validated_data)
        create_audit_log(actor=WorkspaceMember.objects.filter(user=request.user.id).first(), action="CREATED LABEL",
                         model=Label.objects.filter(id=label.id).first()
                         )
        return Response(data={"detail": "Label yaratildi",
                              'id':label.id}, status=HTTP_201_CREATED)


@extend_schema(tags=['Label'])
class LabelDestroyApiView(DestroyAPIView):
    serializer_class = LabelDestroySerilalizer
    queryset = Label.objects.all()
    permission_classes = (IsOwnerManagerFormLabel,)


    def delete(self, request, *args, **kwargs):
        instance = Label.objects.filter(id=self.kwargs['pk']).first()
        create_audit_log(
            actor=WorkspaceMember.objects.filter(user=request.user.id).first(),
            action="DELETED LABEL",
            model=instance
        )
        instance.delete()

        return Response(
            data={"detail": "Label o'chirildi"},
            status=HTTP_200_OK
        )

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


