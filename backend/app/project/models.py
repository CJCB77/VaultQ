from django.db import models
from django.conf import settings


def document_upload_path(instance, filename):
    """Generate upload path for documents"""
    return f'projects/{instance.project.id}/documents/{filename}'


class Project(models.Model):
    """Project model for organizing documents and vector stores"""
    name = models.CharField(
        max_length=255,
        help_text="Name of the project",
        unique=True
    )
    description = models.TextField(
        blank=True,
        help_text="Detailed description of the problem"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE,
        related_name='projects',
        help_text="Owner of the project"
    )
    chroma_collection = models.CharField(
        max_length=255, 
        blank=True,
        help_text="Name of the associated Chroma collection"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at'] # Newest projects first
        indexes = [
            models.Index(fields=['created_at','user'])
        ]

    def __str__(self):
        return self.name


class Document(models.Model):
    """Document model for handling project related files"""

    class ProcessingStatus(models.TextChoices):
        PENDING = 'pending', 'Pending'
        PROCESSING = 'processing', 'Processing',
        COMPLETED = 'completed', 'Completed'
        FAILED = 'failed', 'Failed'

    name = models.CharField(
        max_length=255,
        help_text="Original File Name"
    )
    project = models.ForeignKey(
        'Project', 
        on_delete=models.CASCADE,
        related_name="documents",
        help_text="Project this document belongs"
    )
    file_path = models.FileField(
        upload_to=document_upload_path,
        help_text="Uploaded document file"
    )
    file_size = models.PositiveIntegerField(
        help_text="File size in bytes"
    )
    content_type = models.CharField(
        max_length=100,
        help_text="MIME type of the file"
    )
    processing_status = models.CharField(
        max_length=200,
        choices=ProcessingStatus.choices,
        default=ProcessingStatus.PENDING,
        help_text="Current processing status"
    )
    chunks_count = models.PositiveIntegerField(
        help_text="Number of chunks created from this document"
    )
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="uploaded_documents",
        help_text="User who uploaded the document"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)