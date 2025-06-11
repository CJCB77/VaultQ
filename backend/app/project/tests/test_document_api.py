"""
Tests for the Document model API
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from project.models import Project

from rest_framework.test import APIClient
from rest_framework import status

from ..models import (
    Project,
    Document,
) 
from django.core.files.uploadedfile import SimpleUploadedFile

from ..serializers import DocumentListSerializer

User = get_user_model()

def get_project_documents_url(project_id):
    """Generate URL for accessing documents of a specific project."""
    return reverse('project:project-documents-list', args=[project_id])

def project_document_download_url(project_id, doc_id):
    """Generate URL for downloading a document of a specific project."""
    return reverse(
        'project:project-documents-download',
        args=[project_id, doc_id]
    )

def get_document_detail_url(project_id, doc_id):
    """Generate URL for document details"""
    return reverse('project:project-documents-detail', 
                   args=[project_id, doc_id])

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
            description="Test project description",
            user=self.user
        )
    
    def test_upload_document_to_project(self):
        """Test uploading a document to a project"""
        pdf_content = b'%PDF-1.4 Test PDF content'
        sample_pdf_file = SimpleUploadedFile(
            name='test.pdf',
            content=pdf_content,
            content_type='application/pdf'
        )

        url = get_project_documents_url(self.project.id)
        res = self.client.post(url, {'file':sample_pdf_file}, format='multipart')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        # Exactly one document should be in the db
        self.assertEqual(Document.objects.count(), 1)
        doc = Document.objects.get(pk=res.data['id'])

        # Srializer output matched model state
        self.assertEqual(doc.name, 'test.pdf')
        self.assertEqual(doc.content_type, 'application/pdf')
        self.assertEqual(doc.file_size, len(pdf_content))
        self.assertEqual(doc.processing_status, Document.ProcessingStatus.PENDING)
        self.assertEqual(doc.uploaded_by, self.user)
        self.assertEqual(doc.project, self.project)
    
    def test_invalid_file_upload(self):
        """Test non-PDF files are rejected"""
        invalid_file = SimpleUploadedFile(
            name='test_image.jpeg',
            content=b'some_binary_content',
            content_type='image/jpeg).'
        )
        url = get_project_documents_url(self.project.id)
        res = self.client.post(url, {'file':invalid_file}, format='multipart')

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(Document.objects.filter(project=self.project).exists())

    def test_documents_limited_to_project(self):
        """Test that only documents for the project are returned when retrieving
        documents for a project"""
        Document.objects.create(
            name="test.pdf",
            file='projects/project1/documents/test.pdf',
            file_size=10,
            content_type='application/pdf',
            processing_status=Document.ProcessingStatus.COMPLETED,
            uploaded_by=self.user,
            project=self.project,
        )
        other_project = Project.objects.create(
            name='Other project',
            description='Other project description',
            user=self.user
        )
        Document.objects.create(
            name="test2.pdf",
            file='projects/project1/documents/test2.pdf',
            file_size=10,
            content_type='application/pdf',
            processing_status=Document.ProcessingStatus.COMPLETED,
            uploaded_by=self.user,
            project=other_project
        )

        url = get_project_documents_url(self.project.id)
        res = self.client.get(url)

        docs = Document.objects.filter(project=self.project)
        serializer = DocumentListSerializer(docs, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_donwload_project_document(self):
        # First upload a file
        content = b'Hello world'
        uploaded_file = SimpleUploadedFile(
            'test.pdf',
            content,
            content_type='application/pdf'
        )
        post_url = get_project_documents_url(self.project.id)
        post = self.client.post(post_url, {'file': uploaded_file}, format='multipart')
        self.assertEqual(post.status_code, status.HTTP_201_CREATED)
        doc_id = post.data['id']

        # Download the file
        url = project_document_download_url(self.project.id, doc_id)
        res = self.client.get(url)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        # Check correct headers
        self.assertEqual(res['Content-Type'], 'application/pdf')
        self.assertIn('attachment;', res['Content-Disposition'])
        # Body is the same
        response_content = b''.join(res.streaming_content)
        self.assertEqual(response_content, content)

    def test_deleting_document(self):
        """Test that a user can delete a document that they own"""
        doc = Document.objects.create(
            name="test.pdf",
            file='projects/project1/documents/test.pdf',
            file_size=10,
            content_type='application/pdf',
            processing_status=Document.ProcessingStatus.COMPLETED,
            uploaded_by=self.user,
            project=self.project,
        )
        url = get_document_detail_url(self.project.id, doc.id)
        
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Document.objects.filter(id=doc.id).exists())

    def test_user_cannot_delete_other_document(self):
        """Test that a user cannot delete a document that they don't own"""
        Document.objects.create(
            name="test.pdf",
            file='projects/project1/documents/test.pdf',
            file_size=10,
            content_type='application/pdf',
            uploaded_by=self.user,
            project=self.project,
        )
        new_user = User.objects.create_user(
            email='test2@example.com',
            password='pass12345',
        )
        other_user_doc = Document.objects.create(
            name="test2.pdf",
            file='projects/project1/documents/test2.pdf',
            file_size=8,
            content_type='application/pdf',
            uploaded_by=new_user,
            project=self.project,
        )

        url = get_document_detail_url(self.project.id, other_user_doc.id)

        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(Document.objects.filter(id=other_user_doc.id).exists())
