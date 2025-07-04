from django.test import TestCase
from django.contrib.auth import get_user_model
from ..models import Project

from django.db.utils import DataError

User = get_user_model()

class ProjectModelTests(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            email='test@test.com', 
            password='testpass'
        ) # type: ignore

    def test_create_project(self):
        """Test creating a project succeeds"""
        project = Project.objects.create(
            user=self.user,
            name='Test Project',
            description='Test description'
        )
        
        self.assertEqual(str(project), 'Test Project')  # Test __str__
        self.assertEqual(project.user.email, 'test@test.com')

    def test_project_name_max_length(self):
        """Test name field max_length constraint"""
        project = Project(name='x' * 256, user=self.user)  # Exceeds default CharField max_length
        
        with self.assertRaises(DataError): 
            project.save()
    
    def test_project_has_auto_timestamps(self):
        """Test that auto_now_add and auto_now fields are not automatically set"""
        project = Project.objects.create(
            name="Test project",
            description="Project description",
            user=self.user
        )
        self.assertIsNotNone(project.created_at)
        self.assertIsNotNone(project.updated_at)