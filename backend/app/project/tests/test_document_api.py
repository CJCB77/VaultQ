"""
Tests for the Document model API
"""
from unittest.mock import patch, MagicMock
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.conf import settings
from django.db import transaction

from project.models import Project

from rest_framework.test import APIClient
from rest_framework import status

from ..models import (
    Project,
    Document,
) 
from django.core.files.uploadedfile import SimpleUploadedFile

from ..serializers import DocumentListSerializer
import tempfile
from pathlib import Path
import shutil
from project.tasks import process_document_task


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

    @classmethod
    def setUpClass(cls):
        """Set up a temporary media directory for the test class."""
        super().setUpClass()
        # Create a clean temp dir and path MEDIA_ROOT into settings
        cls._orig_media_root = settings.MEDIA_ROOT
        cls._orig_chroma_root = settings.CHROMA_ROOT

        cls._temp_media = tempfile.mkdtemp(prefix="test_media_")
        cls._temp_chroma = tempfile.mkdtemp(prefix="test_chroma_")

        settings.MEDIA_ROOT = cls._temp_media
        settings.CHROMA_ROOT = cls._temp_chroma

    def setUp(self):
        """Set up client and user for test
        - Create a user
        - Create a client and authenticate as the user
        - Create a project for the user
        """
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
    
    @classmethod
    def tearDownClass(cls):
        """Clean up temporary media folder and restore original settings."""
        super().tearDownClass()
        # Remove the temp dir and restore the original
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        shutil.rmtree(settings.CHROMA_ROOT, ignore_errors=True)

        settings.MEDIA_ROOT = cls._orig_media_root
        settings.CHROMA_ROOT = cls._orig_chroma_root

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
        other_project = Project.objects.create(
            name="Test Project 2",
            description="Test project description",
            user=new_user
        )
        other_user_doc = Document.objects.create(
            name="test2.pdf",
            file='projects/project1/documents/test2.pdf',
            file_size=8,
            content_type='application/pdf',
            uploaded_by=new_user,
            project=other_project,
        )

        url = get_document_detail_url(other_project.id, other_user_doc.id)

        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(Document.objects.filter(id=other_user_doc.id).exists())
    
    def test_cannot_upload_another_users_project(self):
        """Test that a user cannot upload a document to another user's project"""
        new_user = User.objects.create_user(
            email='test2@example.com',
            password='pass12345',
        )
        other_project = Project.objects.create(
            name="Test Project 2",
            description="Test project description",
            user=new_user
        )
        file_upload = SimpleUploadedFile(
            name='test.pdf',
            content=b'Foo',
            content_type='application/pdf'
        )

        url = get_project_documents_url(other_project.id)
        res = self.client.post(url, {'file': file_upload}, format='multipart')

        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    @patch('project.views.process_document_task.delay')
    def test_upload_trigger_celery_task(self, mock_delay):
        """Uploading a valid PDF should enqueue the ingestion Celery task."""
        # Prepare a small PDF
        pdf_content = b'%PDF-1.4 Test PDF'
        uploaded = SimpleUploadedFile(
            name='foo.pdf',
            content=pdf_content,
            content_type='application/pdf'
        )
        url = get_project_documents_url(self.project.id)
        res = self.client.post(url, {'file': uploaded}, format='multipart')

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        # Exactly one Document created
        self.assertEqual(Document.objects.count(), 1)
        doc = Document.objects.first()

        # Celery task.delay should be called once with this doc’s ID
        mock_delay.assert_called_once_with(doc.id)
    
    @patch('project.views.process_document_task.delay')
    def test_invalid_upload_does_not_trigger_task(self, mock_delay):
        """Uploading a non‐PDF must be rejected and not enqueue any task."""
        bad = SimpleUploadedFile(
            name='foo.jpg',
            content=b'GIF89a',
            content_type='image/jpeg'
        )
        url = get_project_documents_url(self.project.id)
        res = self.client.post(url, {'file': bad}, format='multipart')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

        # No Document created, so delay() should never have been called
        self.assertEqual(Document.objects.count(), 0)
        mock_delay.assert_not_called()
    
    @patch('project.tasks.PyPDFLoader')
    @patch('project.tasks.RecursiveCharacterTextSplitter')
    @patch('project.tasks.Chroma')
    def test_process_document_task_success(
        self,
        mock_chroma,
        mock_splitter_cls,
        mock_pdfloader_cls,
    ):
        """
        Running process_document_task on a valid document should:
            - create the project.chroma_collection
            - mark status COMPLETED
            - set correct chunks_count
            - create the chroma folder in CHROMA_ROOT
        """
        # 1) Create a dummy Document
        #    Use a small pdf file so PyPDFLoader/TextLoader behave the same
        content = b"one two three"
        uploaded = SimpleUploadedFile(
            'foo.pdf', content, content_type='application/pdf'
        )
        doc = Document.objects.create(
            project=self.project,
            uploaded_by=self.user,
            name=uploaded.name,
            file=uploaded,
            file_size=len(content),
            content_type='application/pdf',
        )
        self.assertEqual(doc.processing_status, Document.ProcessingStatus.PENDING)

        # 2) Stub loader.load() → single-page list
        fake_page = MagicMock()
        mock_pdfloader = mock_pdfloader_cls.return_value
        mock_pdfloader.load.return_value = [fake_page]

        # 3) Stub splitter.split_documents() -> 3 fake chunks
        fake_chunks = [
            MagicMock(page_content='A'),
            MagicMock(page_content='B'),
            MagicMock(page_content='C')
        ]
        mock_splitter = mock_splitter_cls.return_value
        mock_splitter.split_documents.return_value = fake_chunks

        # 4) Stub Chroma.from_documents() -> fake store
        fake_store = MagicMock()
        mock_chroma.from_documents.return_value = fake_store

        # 5) Call the task in a comitted transaction
        with transaction.atomic():
            process_document_task(doc.id)
        
        # 6) Refresh from DB and project
        doc.refresh_from_db()
        self.project.refresh_from_db()

        self.assertEqual(
            doc.processing_status,
            Document.ProcessingStatus.COMPLETED
        )
        self.assertEqual(doc.chunks_count, len(fake_chunks))
        
        # Project chroma_collection must be now set
        self.assertTrue(self.project.chroma_collection)

        # The Chroma folder on disk must exist
        vectordir = Path(settings.CHROMA_ROOT) / f"projects/{self.project.id}"
        self.assertTrue(vectordir.exists(), f"{vectordir} missing")

        # Check from_documents was called with our fake_chunks
        mock_chroma.from_documents.assert_called_once()
    
    @patch('project.tasks.RecursiveCharacterTestSplitter.split_documents')
    @patch('project.tasks.PyPDFLoader')
    def test_process_document_task_failure(
            self,
            mock_pdfloader_cls,
            mock_split_documents,
    ):
        """
        If chunking blows up, the task should mark the doc as FAILED
        """
        content = b"broken content"
        uploaded = SimpleUploadedFile(
            'bad.pdf', content, content_type='application/pdf'
        )
        doc = Document.objects.create(
            project      = self.project,
            uploaded_by  = self.user,
            name         = uploaded.name,
            file         = uploaded,
            file_size    = len(content),
            content_type = 'application/pdf',
        )
        self.assertEqual(doc.processing_status, Document.ProcessingStatus.PENDING)
        # Stub loader.load() → valid page, but splitter errors
        mock_pdfloader = mock_pdfloader_cls.return_value
        mock_pdfloader.load.return_value = ['page1']
        mock_split_documents.side_effect = RuntimeError("split boom")
        
        # now run the task under a transaction so that our DB writes get committed
        with self.assertRaises(RuntimeError):
            with transaction.atomic():
                process_document_task(doc.id)
                
        # Doc must be marked FAILED
        doc.refresh_from_db()
        self.assertEqual(
            doc.processing_status,
            Document.ProcessingStatus.FAILED
        )