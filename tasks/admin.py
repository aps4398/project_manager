from django.contrib import admin
from django.utils.html import format_html
from .models import Task, Comment, Attachment, Label, Component, Version

class CommentInline(admin.TabularInline):
    model = Comment
    extra = 0
    readonly_fields = ['author', 'created_at']
    fields = ['author', 'content', 'created_at']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('author')

class AttachmentInline(admin.TabularInline):
    model = Attachment
    extra = 0
    readonly_fields = ['uploaded_by', 'uploaded_at']
    fields = ['file', 'uploaded_by', 'uploaded_at']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('uploaded_by')

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = [
        'key', 'truncated_title', 'project', 'issue_type_badge', 
        'status_badge', 'priority_badge', 'assignee', 'due_date', 'action_buttons'
    ]
    list_filter = ['status', 'priority', 'issue_type', 'project', 'due_date']
    search_fields = ['key', 'title', 'description']
    filter_horizontal = ['labels', 'components', 'fix_versions', 'affects_versions']
    readonly_fields = ['key', 'created_at', 'updated_at']
    inlines = [CommentInline, AttachmentInline]
    list_per_page = 25
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('key', 'title', 'description', 'project', 'assignee')
        }),
        ('Classification', {
            'fields': ('issue_type', 'status', 'priority', 'labels')
        }),
        ('Tracking', {
            'fields': ('epic', 'sprint', 'story_points', 'time_estimate', 'time_logged')
        }),
        ('Components & Versions', {
            'fields': ('components', 'fix_versions', 'affects_versions')
        }),
        ('Dates', {
            'fields': ('due_date', 'created_at', 'updated_at')
        }),
    )
    
    def truncated_title(self, obj):
        return obj.title[:50] + '...' if len(obj.title) > 50 else obj.title
    truncated_title.short_description = 'Title'
    
    def issue_type_badge(self, obj):
        colors = {
            'story': 'primary',
            'task': 'info',
            'bug': 'danger',
            'epic': 'warning',
            'subtask': 'secondary'
        }
        return format_html(
            '<span class="badge bg-{}">{}</span>',
            colors.get(obj.issue_type, 'secondary'),
            obj.get_issue_type_display()
        )
    issue_type_badge.short_description = 'Type'
    
    def status_badge(self, obj):
        colors = {
            'backlog': 'secondary',
            'todo': 'primary',
            'in_progress': 'warning',
            'in_review': 'info',
            'done': 'success'
        }
        return format_html(
            '<span class="badge bg-{}">{}</span>',
            colors.get(obj.status, 'secondary'),
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def priority_badge(self, obj):
        colors = {
            'lowest': 'secondary',
            'low': 'info',
            'medium': 'primary',
            'high': 'warning',
            'highest': 'danger'
        }
        return format_html(
            '<span class="badge bg-{}">{}</span>',
            colors.get(obj.priority, 'secondary'),
            obj.get_priority_display()
        )
    priority_badge.short_description = 'Priority'
    
    def action_buttons(self, obj):
        return format_html(
            '<div class="btn-group">'
            '<a href="/admin/tasks/task/{}/change/" class="btn btn-sm btn-outline-secondary">Edit</a>'
            '<a href="/admin/tasks/task/{}/delete/" class="btn btn-sm btn-outline-danger">Delete</a>'
            '</div>',
            obj.id, obj.id
        )
    action_buttons.short_description = 'Actions'
    
    class Media:
        css = {
            'all': (
                'https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css',
                'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css',
            )
        }
        js = (
            'https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js',
        )

@admin.register(Label)
class LabelAdmin(admin.ModelAdmin):
    list_display = ['name', 'color', 'color_display', 'task_count']
    list_editable = ['color']
    search_fields = ['name']
    
    def color_display(self, obj):
        return format_html(
            '<span class="badge" style="background-color: {}; color: white;">{}</span>',
            obj.color, obj.color
        )
    color_display.short_description = 'Color Preview'
    
    def task_count(self, obj):
        return obj.task_set.count()
    task_count.short_description = 'Tasks'

@admin.register(Component)
class ComponentAdmin(admin.ModelAdmin):
    list_display = ['name', 'project', 'task_count']
    list_filter = ['project']
    search_fields = ['name', 'project__name']
    
    def task_count(self, obj):
        return obj.task_set.count()
    task_count.short_description = 'Tasks'

@admin.register(Version)
class VersionAdmin(admin.ModelAdmin):
    list_display = ['name', 'project', 'is_released', 'release_date', 'task_count']
    list_filter = ['project', 'is_released']
    list_editable = ['is_released']
    search_fields = ['name', 'project__name']
    
    def task_count(self, obj):
        return obj.fix_tasks.count() + obj.affects_tasks.count()
    task_count.short_description = 'Tasks'

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['task', 'author', 'truncated_content', 'created_at']
    list_filter = ['created_at', 'author']
    search_fields = ['task__title', 'content', 'author__username']
    
    def truncated_content(self, obj):
        return obj.content[:75] + '...' if len(obj.content) > 75 else obj.content
    truncated_content.short_description = 'Content'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('task', 'author')

@admin.register(Attachment)
class AttachmentAdmin(admin.ModelAdmin):
    list_display = ['task', 'file_name', 'uploaded_by', 'uploaded_at']
    list_filter = ['uploaded_at', 'uploaded_by']
    search_fields = ['task__title', 'file']
    
    def file_name(self, obj):
        return obj.file.name.split('/')[-1]
    file_name.short_description = 'File Name'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('task', 'uploaded_by')