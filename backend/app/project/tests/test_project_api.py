"""
Tests for the Project API functionality
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status

from project.models import Project
from project.serializers import (
    ProjectDetailSerializer,
    ProjectListSerializer
)

USER = get_user_model()
PROJECTS_URL = reverse('project:project-list')

def create_project_details_url(project_id):
    return reverse('project:project-detail', args=[project_id])

def create_sample_project(user, **params):
    default_project = {
        "name":"Test Project",
        "description":"Test project description",
        "user":user
    }
    default_project.update(params)

    project = Project.objects.create(**default_project)
    return project

class PublicProjectApiTests(TestCase):
    """Test unauthenticated API requests"""

    def setUp(self):
        self.client = APIClient()
    
    def test_auth_required(self):
        """Test that auth is required to retrieve projects"""
        res = self.client.get(PROJECTS_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

class PrivateProjectApiTests(TestCase):
    """Test for our project api endpoints"""

    def setUp(self):
        self.client = APIClient()
        self.user = USER.objects.create_user(
            email="test@example.com",
            password="test12345"
        ) 
        self.client.force_authenticate(user=self.user)
    
    def test_get_projects(self):
        """Test retrieving a list of projects"""
        create_sample_project(user=self.user)
        create_sample_project(user=self.user, name="Another project")
        
        res = self.client.get(PROJECTS_URL)

        projects = Project.objects.all().order_by("-created_at")
        serializer = ProjectListSerializer(projects, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data) 
    
    def test_get_current_user_projects_only(self):
        """Test retrieving only the projects of the current user"""
        create_sample_project(user=self.user)
        new_user = USER.objects.create_user(
            email="test2@example.com",
            password="pass12345",
        ) 
        create_sample_project(user=new_user, name="Another user's project")
        
        res = self.client.get(PROJECTS_URL)

        projects = Project.objects.filter(user=self.user)
        serializer = ProjectListSerializer(projects, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data) 

    def test_create_project(self):
        """Test creating a project for the authenticated user"""
        payload = {
            "name":"Test Project",
            "description":"Test project description",
        }

        res = self.client.post(PROJECTS_URL, payload)
        project = Project.objects.get(id=res.data['id']) 

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        for key, value in payload.items():
            self.assertEqual(getattr(project, key), value)
        
        self.assertEqual(project.user, self.user) 

    def test_project_name_unique(self):
        """Test that creating a project with a name that already exists
        raises an error
        """
        create_sample_project(name="Test", user=self.user)
        payload = {
            "name":"Test",
            "description":"Test project description",
            "user":self.user
        }


        res = self.client.post(PROJECTS_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get_project_details(self):
        """Test retrieving the details of a specific project"""
        project = create_sample_project(user=self.user)
        serializer = ProjectDetailSerializer(project)
        project_detail_url = create_project_details_url(project_id=project.id)  

        res = self.client.get(project_detail_url)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data) 

    def test_full_update_project_details(self):
        """Test fully updating a project's details for the authenticated user"""
        project = create_sample_project(
            user=self.user,
            name='Test', 
            description='Test description'
        )
        payload = {
            "name":"Test Update",
            "description":"Test project update",
            "user":self.user
        }
        url = create_project_details_url(project_id=project.id) 
        
        res = self.client.put(url, payload)
        project.refresh_from_db()

        serializer = ProjectDetailSerializer(project)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data) 

        
    def test_partial_update_project_details(self):
        """Test partially updating a project's details for the authenticated user"""
        project = create_sample_project(
            user=self.user,
            name='Test', 
            description='Test description'
        )
        payload = {
            "description":"A new description"
        }
        url = create_project_details_url(project_id=project.id) 

        res = self.client.patch(url, payload)
        project.refresh_from_db()

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(project.description, payload['description']) 

    def test_project_user_is_readonly(self):
        """Test that a project's user is read-only and cannot be changed"""
        project = create_sample_project(
            user=self.user,
        )
        new_user = USER.objects.create_user(
            email="test2@example.com",
            password="pass12345"
        )  # type: ignore
        payload = {
            "user": new_user
        }
        url = create_project_details_url(project_id=project.id) 
        res = self.client.patch(url, payload)
        project.refresh_from_db()

        self.assertEqual(project.user, self.user) 

    def test_delete_project(self):
        """Test that an authenticated user can delete a project"""
        project = create_sample_project(
            user=self.user,
        )
        url = create_project_details_url(project_id=project.id) 

        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Project.objects.filter(id=project.id).exists())

    def test_deleting_other_user_project_error(self):
        """Test that deleting a project that is owned by another user raises
        a permissions error
        """
        create_sample_project(
            user=self.user,
        )
        new_user = USER.objects.create_user(
            email="test2@example.com",
            password="pass12345"
        ) # type: ignore
        project = create_sample_project(
            user=new_user,
            name="Other user's project"
        ) 
        url = create_project_details_url(project_id=project.id) 

        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Project.objects.filter(id=project.id).exists())

    def test_create_project_invalid_name(self):
        res = self.client.post(PROJECTS_URL, {'name':''})
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)