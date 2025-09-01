from django.db import models
from django.urls import reverse
from django.conf import settings
from django.utils import timezone
from django.contrib.auth import get_user_model

User = get_user_model()

class Project(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='owned_projects'
    )
    members = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='projects',
        blank=True
    )
    # REMOVE the default value - it causes the unique constraint error!
    key = models.CharField(max_length=10, unique=True)  # Removed default='PROJ'
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)    
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        # Only generate key if it doesn't exist
        if not self.key:
            # Generate base key from name
            if self.name:
                # Clean the name - take only letters, make uppercase, max 3 chars
                base_key = ''.join([c.upper() for c in self.name if c.isalpha()])[:3]
                if not base_key:  # If no letters found
                    base_key = 'PROJ'
            else:
                base_key = 'PROJ'
            
            # Find a unique key
            key = base_key
            counter = 1
            # Keep trying until we find a unique key
            while Project.objects.filter(key=key).exclude(pk=self.pk).exists():
                key = f"{base_key}{counter}"
                counter += 1
            self.key = key
        
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        return reverse('projects:project_detail', kwargs={'pk': self.pk})


class Epic(models.Model):
    class Status(models.TextChoices):
        TODO = 'todo', 'To Do'
        IN_PROGRESS = 'in_progress', 'In Progress'
        DONE = 'done', 'Done'
    
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='epics')
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.TODO)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ['name', 'project']
    
    def __str__(self):
        return f"{self.name} ({self.project.key})"
    
    def get_absolute_url(self):
        return reverse('projects:epic_detail', kwargs={'pk': self.pk})


class Sprint(models.Model):
    name = models.CharField(max_length=200)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='sprints')
    goal = models.TextField(blank=True)
    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(default=False)
    is_completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-start_date']
    
    def __str__(self):
        return f"{self.name} ({self.project.key})"
    
    def get_absolute_url(self):
        return reverse('projects:sprint_detail', kwargs={'pk': self.pk})
    
    def clean(self):
        from django.core.exceptions import ValidationError
        if self.start_date and self.end_date and self.start_date > self.end_date:
            raise ValidationError("End date cannot be before start date.")
    
    def save(self, *args, **kwargs):
        # Ensure only one active sprint per project
        if self.is_active:
            Sprint.objects.filter(project=self.project, is_active=True).exclude(pk=self.pk).update(is_active=False)
        
        # Auto-complete if end date is in past
        if self.end_date and self.end_date < timezone.now().date():
            self.is_completed = True
            self.is_active = False
            
        super().save(*args, **kwargs)
    
    @property
    def duration_days(self):
        if self.start_date and self.end_date:
            return (self.end_date - self.start_date).days + 1
        return 0