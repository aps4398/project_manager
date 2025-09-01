from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, TemplateView
from django.urls import reverse_lazy
from django.contrib import messages
from django.db import models
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from .models import Task, Comment, Label, Component, Version
from .forms import TaskForm, CommentForm, TaskFilterForm
from projects.models import Project, Sprint, Epic  # Import from projects app
class TaskListView(LoginRequiredMixin, ListView):
    model = Task
    context_object_name = 'tasks'
    template_name = 'tasks/task_list.html'
    
    def get_queryset(self):
        queryset = Task.objects.filter(
            models.Q(project__owner=self.request.user) | 
            models.Q(project__members=self.request.user) |
            models.Q(assignee=self.request.user)
        ).distinct().select_related('project', 'assignee', 'epic', 'sprint')
        
        #Apply filters
        self.filter_form = TaskFilterForm(self.request.GET, project=None)
        if self.filter_form.is_valid():
            status = self.filter_form.cleaned_data.get('status')
            priority = self.filter_form.cleaned_data.get('priority')
            issue_type = self.filter_form.cleaned_data.get('issue_type')
            assignee = self.filter_form.cleaned_data.get('assignee')
            labels = self.filter_form.cleaned_data.get('labels')
            
            if status:
                queryset = queryset.filter(status=status)
            if priority:
                queryset = queryset.filter(priority=priority)
            if issue_type:
                queryset = queryset.filter(issue_type=issue_type)
            if assignee:
                queryset = queryset.filter(assignee=assignee)
            if labels:
                queryset = queryset.filter(labels__in=labels).distinct()
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter_form'] = self.filter_form
        
        # Add counts for dashboard
        context['todo_count'] = self.get_queryset().filter(status='todo').count()
        context['in_progress_count'] = self.get_queryset().filter(status='in_progress').count()
        context['in_review_count'] = self.get_queryset().filter(status='in_review').count()
        context['done_count'] = self.get_queryset().filter(status='done').count()
        context['backlog_count'] = self.get_queryset().filter(status='backlog').count()
        context['total_count'] = self.get_queryset().count()
        
        return context

class TaskKanbanView(LoginRequiredMixin, TemplateView):
    template_name = 'tasks/task_kanban.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project_id = self.kwargs.get('project_id')
        
        if project_id:
            project = get_object_or_404(Project, id=project_id)
            context['project'] = project
            
            # Get tasks for each status column
            columns = {}
            for status_value, status_label in Task.Status.choices:
                tasks = Task.objects.filter(
                    project=project,
                    status=status_value
                ).select_related('assignee', 'epic', 'sprint')
                columns[status_value] = {
                    'label': status_label,
                    'tasks': tasks
                }
            
            context['columns'] = columns
        
        return context

class TaskDetailView(LoginRequiredMixin, DetailView):
    model = Task
    context_object_name = 'task'
    template_name = 'tasks/task_detail.html'
    
    def get_queryset(self):
        return Task.objects.filter(
            models.Q(project__owner=self.request.user) | 
            models.Q(project__members=self.request.user) |
            models.Q(assignee=self.request.user)
        ).distinct().select_related('project', 'assignee', 'epic', 'sprint')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['comment_form'] = CommentForm()
        return context

class TaskCreateView(LoginRequiredMixin, CreateView):
    model = Task
    form_class = TaskForm
    template_name = 'tasks/task_form.html'
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        project_id = self.kwargs.get('project_id')
        if project_id:
            # Fix: Use proper Q object filtering
            project = Project.objects.filter(
                models.Q(owner=self.request.user) | models.Q(members=self.request.user),
                id=project_id
            ).first()
            if project:
                kwargs['project'] = project
        return kwargs
    
    def form_valid(self, form):
        project_id = self.kwargs.get('project_id')
        if project_id:
            # Fix: Use proper Q object filtering
            project = Project.objects.filter(
                models.Q(owner=self.request.user) | models.Q(members=self.request.user),
                id=project_id
            ).first()
            if project:
                form.instance.project = project
        messages.success(self.request, 'Task created successfully!')
        return super().form_valid(form)

class TaskUpdateView(LoginRequiredMixin, UpdateView):
    model = Task
    form_class = TaskForm
    template_name = 'tasks/task_form.html'
    
    def get_queryset(self):
        return Task.objects.filter(
            models.Q(project__owner=self.request.user) | 
            models.Q(project__members=self.request.user)
        ).distinct()
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['project'] = self.object.project
        return kwargs
    
    def form_valid(self, form):
        messages.success(self.request, 'Task updated successfully!')
        return super().form_valid(form)

class CommentCreateView(LoginRequiredMixin, CreateView):
    model = Comment
    form_class = CommentForm
    
    def form_valid(self, form):
        form.instance.author = self.request.user
        # Fix: Use proper Q object filtering
        task = Task.objects.filter(
            models.Q(project__owner=self.request.user) | 
            models.Q(project__members=self.request.user) |
            models.Q(assignee=self.request.user),
            id=self.kwargs['task_id']
        ).first()
        if task:
            form.instance.task = task
            messages.success(self.request, 'Comment added successfully!')
            return super().form_valid(form)
        else:
            messages.error(self.request, 'Task not found or access denied!')
            return redirect('projects:project_list')
    
    def get_success_url(self):
        return reverse_lazy('tasks:task_detail', kwargs={'pk': self.object.task.id})


@method_decorator(csrf_exempt, name='dispatch')
class UpdateTaskStatusView(LoginRequiredMixin, UpdateView):
    model = Task
    fields = ['status']
    
    def post(self, request, *args, **kwargs):
        task = self.get_object()
        new_status = request.POST.get('status')
        
        if new_status in dict(Task.Status.choices):
            task.status = new_status
            task.save()
            return JsonResponse({'success': True, 'new_status': task.get_status_display()})
        
        return JsonResponse({'success': False, 'error': 'Invalid status'})

@require_POST
def log_time(request, pk):
    task = get_object_or_404(Task, pk=pk)
    hours = request.POST.get('hours', 0)
    
    try:
        hours = float(hours)
        from datetime import timedelta
        time_logged = timedelta(hours=hours)
        task.time_logged += time_logged
        task.save()
        messages.success(request, f'Logged {hours} hours to {task.key}')
    except ValueError:
        messages.error(request, 'Invalid time format')
    
    return redirect('tasks:task_detail', pk=task.pk)