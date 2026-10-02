from django.urls import path
from rest_framework.views import APIView

from task.views import TaskCreateApiView, TaskListAdminApiView, TaskRetrieveUpdateDestroy, \
    ChangeAssignee, ChangePriority, ChangeDeadLine, ChangeStatus, DeleteTaskApiView, AttachLabelToTask, \
    LabelListCreateApiView, LabelDestroyApiView, LabelListApiView

urlpatterns = [
    path('', TaskCreateApiView.as_view()),  # admin
    path('list/', TaskListAdminApiView.as_view()),  # team_lead
    path('<int:pk>/', TaskRetrieveUpdateDestroy.as_view()),  # retrieve tasks
    path('change_assignee/<int:task_id>/<int:new_assignee>', ChangeAssignee.as_view()),  # change task assignee
    path('change_priority/<int:task_id>/', ChangePriority.as_view()),  # ChangePriority
    path('change_deadline/<int:task_id>/', ChangeDeadLine.as_view()),  # change tasks deadline
    path('change_status/<int:task_id>/', ChangeStatus.as_view()),  # change tasks status
    path('delete_task/<int:task_id>/', DeleteTaskApiView.as_view()),  # delete tasks
    path('attach_label/',AttachLabelToTask.as_view(),),
    path('labels/post',LabelListCreateApiView.as_view()),
    path('labels/delete/<int:pk>',LabelDestroyApiView.as_view()),
    path('labels/',LabelListApiView.as_view()),
]
