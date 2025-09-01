from django.urls import path
from . import views

app_name = 'tasks'

urlpatterns = [
    path('', views.TaskListView.as_view(), name='task_list'),
    path('create/<int:project_id>/', views.TaskCreateView.as_view(), name='task_create'),
    path('<int:pk>/', views.TaskDetailView.as_view(), name='task_detail'),
    path('<int:pk>/update/', views.TaskUpdateView.as_view(), name='task_update'),
    path('<int:task_id>/comment/', views.CommentCreateView.as_view(), name='comment_create'),
    path('kanban/<int:project_id>/', views.TaskKanbanView.as_view(), name='task_kanban'),
    path('<int:pk>/update-status/', views.UpdateTaskStatusView.as_view(), name='update_task_status'),
    path('<int:pk>/log-time/', views.log_time, name='log_time'),
]