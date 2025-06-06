from django.db import models
from django.conf import settings


class Project(models.Model):
    """Project model for organizing documents and vector stores"""
    name = models.CharField(
        max_length=255,
        help_text="Name of the project"
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