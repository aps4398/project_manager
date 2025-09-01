from django.test import TestCase
from django.contrib.auth import get_user_model
from .models import Project

class ProjectModelTest(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='testuser', password='testpass123'
        )
    
    def test_create_project(self):
        project = Project.objects.create(
            name='Test Project',
            description='Test Description',
            owner=self.user
        )
        self.assertEqual(project.name, 'Test Project')
        self.assertEqual(project.owner, self.user)
        