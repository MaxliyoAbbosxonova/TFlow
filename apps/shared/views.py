from rest_framework import status
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.views import APIView

from .models import FileUpload
from .permissions import IsProjectWorkspaceMember
from .serializers import MultipleFileUploadSerializer, FileUploadSerializer


class MultipleFileUploadView(APIView):
    # Allow file uploads (DRF uses MultiPartParser by default for form-data)
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, *args, **kwargs):
        # Initialize serializer with request data (files)
        serializer = MultipleFileUploadSerializer(data=request.data)

        if serializer.is_valid():
            # Save files using the serializer's create() method
            file_uploads = serializer.save()
            # Return serialized data for the uploaded files
            return Response(
                FileUploadSerializer(file_uploads, many=True).data,
                status=status.HTTP_201_CREATED
            )

            # Return errors if validation fails
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class FileUploadViewSet(viewsets.ModelViewSet):
    queryset = FileUpload.objects.all()  # List all uploaded files
    serializer_class = FileUploadSerializer

    @action(
        detail=True,
        methods=["POST"],
        parser_classes=[MultiPartParser],
        url_path=r"upload/(?P<filename>[a-zA-Z0-9_]+\.mp3)",
    )
    def upload(self, request, **kwargs):
        track = self.get_object()

        if "file" not in request.data:
            raise ValidationError("There is no file in the HTTP body.")

        file = request.data["file"]
        track.file.save(file.name, file)
        return Response(FileUploadSerializer(track).data)


from django.db.models import Avg, Count, DurationField, ExpressionWrapper, F, Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

# O'zingizning modellaringizga moslang:
from project.models import Project
from task.models import Task

ONE = 'done'  # Task.status ichidagi "tugallangan" qiymati


def _hours(delta):
    """timedelta -> soat (float), None bo'lsa None."""
    return round(delta.total_seconds() / 3600, 2) if delta else None


COMPLETION_TIME = ExpressionWrapper(
    F('completed_at') - F('created_at'), output_field=DurationField()
)


@extend_schema(tags=['Statistics'])
class ProjectStatisticsApiView(APIView):
    permission_classes = (IsAuthenticated, IsProjectWorkspaceMember,)

    def get(self, request, pk):
        project = get_object_or_404(Project, pk=pk)
        now = timezone.now()
        tasks = Task.objects.filter(project=project)
        overdue_q = Q(deadline__lt=now) & ~Q(status=Task.Workflow.DONE)

        # 1-3: jami, completed, overdue
        totals = tasks.aggregate(
            total=Count('id'),
            completed=Count('id', filter=Q(status=Task.Workflow.DONE)),
            overdue=Count('id', filter=overdue_q),
        )

        # 4: statuslar bo'yicha
        by_status = tasks.values('status').annotate(count=Count('id')).order_by('status')

        # 5: priority bo'yicha
        by_priority = tasks.values('priority').annotate(count=Count('id')).order_by('priority')

        # 6 + 8: har bir employee bo'yicha (team performance ham shu yerdan)
        per_employee = (
            tasks.values('assignee_id', 'assignee__user__email')
            .annotate(
                total=Count('id'),
                completed=Count('id', filter=Q(status=Task.Workflow.DONE)),
                overdue=Count('id', filter=overdue_q),
                avg_time=Avg(COMPLETION_TIME, filter=Q(status=Task.Workflow.DONE, completed_at__isnull=False)),
            )
            .order_by('-completed')
        )
        employees = []
        for row in per_employee:
            rate = round(row['completed'] / row['total'] * 100, 1) if row['total'] else 0
            employees.append({
                'employee_id': row['assignee_id'],
                'email': row['assignee__user__email'],
                'total': row['total'],
                'completed': row['completed'],
                'overdue': row['overdue'],
                'completion_rate': rate,
                'avg_completion_hours': _hours(row['avg_time']),
            })

        # 7: o'rtacha completion time
        avg_time = tasks.filter(status=Task.Workflow.DONE, completed_at__isnull=False).aggregate(
            avg=Avg(COMPLETION_TIME)
        )['avg']

        total = totals['total']
        return Response({
            'project': project.pk,
            'total_tasks': total,
            'completed_tasks': totals['completed'],
            'overdue_tasks': totals['overdue'],
            'completion_rate': round(totals['completed'] / total * 100, 1) if total else 0,
            'by_status': list(by_status),
            'by_priority': list(by_priority),
            'avg_completion_hours': _hours(avg_time),
            'by_employee': employees,
            'team_performance': {
                'top_performer': employees[0] if employees else None,
                'members_count': len(employees),
            },
        })
