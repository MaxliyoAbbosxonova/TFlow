from django.db.migrations import serializer
from django.db.models import Model
from drf_spectacular.utils import extend_schema
from rest_framework.generics import RetrieveUpdateDestroyAPIView, CreateAPIView, ListAPIView, ListCreateAPIView
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.status import HTTP_200_OK, HTTP_404_NOT_FOUND, HTTP_201_CREATED
from rest_framework.views import APIView

from services.tasks import change_status, change_assignee, change_priority, change_deadline, delete_task, create_task
from shared.permissions import Tasks_Create_Permission, \
    Tasks_CRUD_Permission
from task.models import Task, Label
from task.serializers import TaskModelSerializer, TaskAdminModelSerializer, \
    ChangeAssigneeSerializer, ChangePrioritySerializer, ChangeDeadLineSerializer, \
    ChangeStatusSerializer, DeleteTaskSerializer, LabelModelSerilalizer, AttachLabelSerilaizer


# Create your views here.


@extend_schema(tags=["Tasks"])
class TaskListApiView(ListAPIView):
    serializer_class = TaskAdminModelSerializer
    queryset = Task.objects.all()
    permission_classes = (IsAdminUser,)
    parser_classes = [MultiPartParser, FormParser]


@extend_schema(tags=["Tasks"])
class TaskCreateApiView(CreateAPIView):
    serializer_class = TaskModelSerializer
    queryset = Task.objects.all()
    parser_classes = [MultiPartParser, FormParser]
    permission_classes = (Tasks_Create_Permission,)

    @extend_schema(
        request=TaskModelSerializer,
        responses=TaskModelSerializer,
    )
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        task=create_task(serializer.validated_data)
        return Response(data=task.data,status=HTTP_201_CREATED)


@extend_schema(tags=["Tasks"])
class TaskRetrieveUpdateDestroy(RetrieveUpdateDestroyAPIView):
    queryset = Task.objects.all()
    serializer_class = TaskModelSerializer
    permission_classes = (Tasks_CRUD_Permission,)


@extend_schema(tags=["Tasks"])
class ChangeAssignee(APIView):
    serializer_class = ChangeAssigneeSerializer

    def patch(self, request, task_id, new_assignee):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        change_assignee(task_id, new_assignee)
        return Response({'detail': "Assignee o`zgartirildi."}, status=HTTP_200_OK)


@extend_schema(tags=["Tasks"])
class ChangePriority(APIView):
    serializer_class = ChangePrioritySerializer

    def patch(self, request, task_id):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        change_priority(task_id, serializer.validated_data['priority'])
        return Response({'detail': "Priority o`zgartirildi."}, status=HTTP_200_OK)


@extend_schema(tags=["Tasks"])
class ChangeDeadLine(APIView):
    serializer_class = ChangeDeadLineSerializer

    def patch(self, request, task_id):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        change_deadline(task_id, serializer.validated_data['deadline'])
        return Response({'detail': "Deadline o`zgartirildi."}, status=HTTP_200_OK)


@extend_schema(tags=["Tasks"])
class ChangeStatus(APIView):
    serializer_class = ChangeStatusSerializer

    def patch(self, request, task_id):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        change_status(task_id, serializer.validated_data['status'])
        return Response({'detail': "Status o`zgartirildi."}, status=HTTP_200_OK)


@extend_schema(tags=['Tasks'])
class DeleteTaskApiView(APIView):
    serializer_class = DeleteTaskSerializer

    def patch(self, request, task_id):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        delete_task(task_id)
        return Response({'detail': "Task o`chirildi"}, status=HTTP_200_OK)


class LabelListCreateApiView(ListCreateAPIView):
    serializer_class = LabelModelSerilalizer
    queryset = Label.objects.all()

class AttachLabelToTask(APIView):
    serializer_class=AttachLabelSerilaizer
    def post(self,request):
        serializer=self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        task=serializer.save()

        return Response(data=task.data,status=HTTP_200_OK)



