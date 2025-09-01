from django import forms
from .models import Task, Comment, Label, Component, Version
from projects.models import Project, Epic, Sprint  # Add this import
from django.conf import settings
class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = [ 'title', 'description', 'issue_type', 'assignee', 'status', 
            'priority', 'story_points', 'time_estimate', 'due_date',
            'epic', 'sprint', 'labels', 'components', 'fix_versions', 'affects_versions'
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'issue_type': forms.Select(attrs={'class': 'form-control'}),
            'assignee': forms.Select(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'priority': forms.Select(attrs={'class': 'form-control'}),
            'story_points': forms.NumberInput(attrs={'class': 'form-control'}),
            'time_estimate': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Hours'}),
            'due_date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'epic': forms.Select(attrs={'class': 'form-control'}),
            'sprint': forms.Select(attrs={'class': 'form-control'}),
            'labels': forms.SelectMultiple(attrs={'class': 'form-control'}),
            'components': forms.SelectMultiple(attrs={'class': 'form-control'}),
            'fix_versions': forms.SelectMultiple(attrs={'class': 'form-control'}),
            'affects_versions': forms.SelectMultiple(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.project = kwargs.pop('project', None)
        super().__init__(*args, **kwargs)
        if self.project:
            self.fields['assignee'].queryset = self.project.members.all()
            self.fields['epic'].queryset = Epic.objects.filter(project=self.project)
            self.fields['sprint'].queryset = Sprint.objects.filter(project=self.project)
            self.fields['components'].queryset = Component.objects.filter(project=self.project)
            self.fields['fix_versions'].queryset = Version.objects.filter(project=self.project)
            self.fields['affects_versions'].queryset = Version.objects.filter(project=self.project)

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 3,
                'placeholder': 'Add a comment...'
            }),
        }

class TaskFilterForm(forms.Form):
    STATUS_CHOICES = [
        ('', 'All Statuses'),
        *Task.Status.choices
    ]
    
    PRIORITY_CHOICES = [
        ('', 'All Priorities'),
        *Task.Priority.choices
    ]
    
    ISSUE_TYPE_CHOICES = [
        ('', 'All Types'),
        *Task.IssueType.choices
    ]
    
    status = forms.ChoiceField(choices=STATUS_CHOICES, required=False, widget=forms.Select(attrs={'class': 'form-control'}))
    priority = forms.ChoiceField(choices=PRIORITY_CHOICES, required=False, widget=forms.Select(attrs={'class': 'form-control'}))
    issue_type = forms.ChoiceField(choices=ISSUE_TYPE_CHOICES, required=False, widget=forms.Select(attrs={'class': 'form-control'}))
    assignee = forms.ModelChoiceField(queryset=None, required=False, widget=forms.Select(attrs={'class': 'form-control'}))
    labels = forms.ModelMultipleChoiceField(queryset=Label.objects.all(), required=False, widget=forms.SelectMultiple(attrs={'class': 'form-control'}))
    
    def __init__(self, *args, **kwargs):
        project = kwargs.pop('project', None)
        super().__init__(*args, **kwargs)
        if project:
            self.fields['assignee'].queryset = project.members.all()