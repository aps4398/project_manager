from django.test import TestCase
from django.contrib.auth import get_user_model
from projects.models import Project
from .models import Task

class TaskModelTest(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='testuser', password='testpass123'
        )
        self.project = Project.objects.create(
            name='Test Project', description='Test', owner=self.user
        )
    
    def test_create_task(self):
        task = Task.objects.create(
            title='Test Task',
            description='Test Description',
            project=self.project,
            assignee=self.user
        )
        self.assertEqual(task.title, 'Test Task')
        self.assertEqual(task.project, self.project)