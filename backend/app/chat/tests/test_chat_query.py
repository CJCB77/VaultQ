"""
Tests for the Chat session API endpoints
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.conf import settings

from rest_framework.test import APIClient
from rest_framework import status

from project.models import Project

import tempfile
import shutil

User = get_user_model()

class RagUnitTests(TestCase):
    """
    Class to test RAG functionality when querying chat
    """
    @classmethod
    def setUpClass(cls):
         """
         1) Setup a temporary media directory for the test class.
         2) Setup a temporary chroma_storage directory for the test class 
         """
         super().setUpClass()
         cls._orig_media_root = settings.MEDIA_ROOT
         cls._orig_chroma_root = settings.CHROMA_ROOT

         cls._temp_media = tempfile.mkdtemp(prefix="test_media_")
         cls._temp_chroma = tempfile.mkdtemp(prefix="temp_chroma_")

         settings.MEDIA_ROOT = cls._temp_media 
         settings.CHROMA_ROOT = cls._temp_chroma 

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(settings.MEDIA_ROOT,ignore_errors=True)
        shutil.rmtree(settings.CHROMA_ROOT, ignore_errors=True)

        settings.MEDIA_ROOT = cls._orig_media_root
        settings.CHROMA_ROOT = cls._orig_chroma_root

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="test@example.com",
            password="pass12345"
        )
        self.project = Project.objects.create(
            name="Test",
            description="description",
            user=self.user
        )
        self.client.force_authenticate(user=self.user)

    def test_run_rag_and_llm_builds_messages(self):
        pass

