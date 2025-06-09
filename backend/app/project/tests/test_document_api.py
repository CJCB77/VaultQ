"""
Tests for the Document model API
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from project.models import Project
import tempfile

from rest_framework.test import APIClient
from rest_framework import status

from ..models import Project 
from django.core.files.uploadedfile import SimpleUploadedFile

from ..serializers import DocumentSerializer

User = get_user_model()

def get_project_documents_url(project_id):
    return reverse('project:project-documents', args=[project_id])

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
    
    def test_upload_document_to_project(self):
        sample_pdf_file = SimpleUploadedFile(
            name='test.pdf',
            content='Test content',
            content_type='application/pdf'
        )
        URL = get_project_documents_url(self.project.id)
        res = self.client.post(URL, sample_pdf_file)

        project_document = Document.objects.get(id=res.id)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(project_document.name, 'test.pdf')
    
    def test_uploaded_files_fit_content_type(self):
        sample_image_file = SimpleUploadedFile(
            name='test_image.jpeg',
            content=b'some_binary_content',
            content_type='image/jpeg).'
        )
        URL = get_project_documents_url(self.project.id)
        res = self.client.post(URL, sample_image_file)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(Document.objects.filter(id=res.id).exists())

    def test_documents_limited_to_project(self):
          Document.objects.create(
            name="test.pdf"
            file = 'projects/project1/documents/test.pdf'
            content_type = 'application/pdf'
            project = self.project
        )
        Document.objects.create(
            name="test2.pdf"
            file = 'projects/project1/documents/test2.pdf'
            content_type = 'application/pdf'
            project = self.project
        )

        URL = get_project_documents_url(self.project.id)
        res = self.client.get(URL)
        documents = Document.objects.filter(project=self.project)
        serializer = DocumentSerializer(documents)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_donwload_project_document(self):
        pass

