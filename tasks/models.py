from django.db import models
from django.urls import reverse
from django.conf import settings
from datetime import timedelta
from projects.models import Project, Epic, Sprint

class Label(models.Model):
    name = models.CharField(max_length=50, unique=True)
    color = models.CharField(max_length=7, default='#6b7280')
    
    def __str__(self):
        return self.name
class Component(models.Model):
    name = models.CharField(max_length=100)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='components')
    description = models.TextField(blank=True)
    
    class Meta:
        unique_together = ['name', 'project']
    
    def __str__(self):
        return f"{self.project.key}: {self.name}"

class Version(models.Model):
    name = models.CharField(max_length=100)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='versions')
    description = models.TextField(blank=True)
    release_date = models.DateField(null=True, blank=True)
    is_released = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ['name', 'project']
    
    def __str__(self):
        return f"{self.project.key}: {self.name}"

class Task(models.Model):
    class Status(models.TextChoices):
        BACKLOG = 'backlog', 'Backlog'
        TODO = 'todo', 'To Do'
        IN_PROGRESS = 'in_progress', 'In Progress'
        IN_REVIEW = 'in_review', 'In Review'
        DONE = 'done', 'Done'
    
    class Priority(models.TextChoices):
        LOWEST = 'lowest', 'Lowest'
        LOW = 'low', 'Low'
        MEDIUM = 'medium', 'Medium'
        HIGH = 'high', 'High'
        HIGHEST = 'highest', 'Highest'
    
    class IssueType(models.TextChoices):
        STORY = 'story', 'Story'
        TASK = 'task', 'Task'
        BUG = 'bug', 'Bug'
        EPIC = 'epic', 'Epic'
        SUBTASK = 'subtask', 'Subtask'
    
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='tasks')
    assignee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_tasks'
    )
    
    # Jira-like fields - make key nullable first
# Change this line:
    key = models.CharField(max_length=20, unique=True, default='TASK')
    epic = models.ForeignKey(Epic, on_delete=models.SET_NULL, null=True, blank=True, related_name='tasks')
    sprint = models.ForeignKey(Sprint, on_delete=models.SET_NULL, null=True, blank=True, related_name='tasks')
    story_points = models.PositiveSmallIntegerField(null=True, blank=True)
    time_estimate = models.DurationField(null=True, blank=True)
    # FIX: Use timedelta for default, not integer
    time_logged = models.DurationField(blank=True, null=True, default=timedelta())


    
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.BACKLOG)
    priority = models.CharField(max_length=10, choices=Priority.choices, default=Priority.MEDIUM)
    issue_type = models.CharField(max_length=10, choices=IssueType.choices, default=IssueType.TASK)
    due_date = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Many-to-many relationships
    labels = models.ManyToManyField(Label, blank=True)
    components = models.ManyToManyField(Component, blank=True)
    fix_versions = models.ManyToManyField(Version, blank=True, related_name='fix_tasks')
    affects_versions = models.ManyToManyField(Version, blank=True, related_name='affects_tasks')
    
    class Meta:
        ordering = ['due_date', 'priority']
    
    def __str__(self):
        return f"{self.key}: {self.title}" if self.key else self.title
    
    def save(self, *args, **kwargs):
        if not self.key and self.project and self.project.key:
            # Generate task key (e.g., "MP-1")
            last_task = Task.objects.filter(project=self.project).order_by('-id').first()
            next_number = 1
            if last_task and last_task.key:
                try:
                    next_number = int(last_task.key.split('-')[1]) + 1
                except (IndexError, ValueError):
                    pass
            self.key = f"{self.project.key}-{next_number}"
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        return reverse('tasks:task_detail', kwargs={'pk': self.pk})

class Comment(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f'Comment by {self.author} on {self.task}'

class Attachment(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField(upload_to='task_attachments/')
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.file.name