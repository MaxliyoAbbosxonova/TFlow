from django.urls import path
from task.views import (
    AttachLabelToTask,
    ChangeAssignee,
    ChangeDeadLine,
    ChangePriority,
    ChangeStatus,
    DeleteTaskApiView,
    LabelDestroyApiView,
    LabelListApiView,
    LabelListCreateApiView,
    TaskCreateApiView,
    TaskListAdminApiView,
    TaskRetrieveUpdateDestroy,
)

urlpatterns = [
    path('', TaskCreateApiView.as_view(), name='task-create'),  # admin
    path('list/', TaskListAdminApiView.as_view(), name='task-list'),  # team_lead
    path('<int:pk>/', TaskRetrieveUpdateDestroy.as_view(), name='task-detail'),  # retrieve tasks
    path('change_assignee/<int:task_id>/<int:new_assignee>', ChangeAssignee.as_view(), name='change-assignee'),
    # change task assignee
    path('change_priority/<int:task_id>/', ChangePriority.as_view(), name='change-priority'),  # ChangePriority
    path('change_deadline/<int:task_id>/', ChangeDeadLine.as_view(), name='change-deadline'),  # change tasks deadline
    path('change_status/<int:task_id>/', ChangeStatus.as_view(), name='task-change-status'),  # change tasks status
    path('delete_task/<int:task_id>/', DeleteTaskApiView.as_view(), name='task-delete'),  # delete tasks
    path('attach_label/', AttachLabelToTask.as_view(), name='label-attach'),
    path('labels/post', LabelListCreateApiView.as_view(), name='label-create'),
    path('labels/delete/<int:pk>', LabelDestroyApiView.as_view(), name='label-delete'),
    path('labels/', LabelListApiView.as_view(), name='label-list'),
]
