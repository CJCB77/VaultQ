"""
Tests for the Document model API
"""
from django.test import TestCase
from django.contrib.auth import get_user_model

from ..models import Project
import tempfile
import os

from rest_framework.test import APIClient
from rest_framework import status

User = get_user_model()

class DocumentModelTest(TestCase):
    """Test cases for Document model"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='test@example.com',
            password='pass12345'
        ) # type: ignore
        self.client.force_authenticate(self.user)

        self.project = Project.objects.create(
            name="Test Project",
            description="Test project description"
        )