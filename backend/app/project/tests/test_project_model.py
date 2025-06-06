from django.test import TestCase
from django.contrib.auth import get_user_model
from ..models import Project

from django.core.exceptions import ValidationError

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
        self.assertEqual(project.owner.email, 'test@test.com')

    def test_project_name_max_length(self):
        """Test name field max_length constraint"""
        project = Project(name='x' * 256, user=self.user)  # Exceeds default CharField max_length
        
        with self.assertRaises(ValidationError): 
            project.save()