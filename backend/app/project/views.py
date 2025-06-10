"""
API Views for the Project model
"""

from django.shortcuts import get_object_or_404
from .models import (
    Project,
    Document
)
from .serializers import (
    ProjectListSerializer,
    ProjectDetailSerializer,
    DocumentDetailSerializer,
    DocumentListSerializer,
    DocumentUploadSerializer
)

from rest_framework import (
    viewsets,
)
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated

class ProjectViewSet(viewsets.ModelViewSet):
    """View for managing project API"""
    queryset = Project.objects.all().order_by('-created_at')
    serializer_class = ProjectDetailSerializer
    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication]

    def get_queryset(self):
        """Retrieve projects for the authenticated user"""
        return self.queryset.filter(user=self.request.user)
    
    def get_serializer_class(self):
        """Return the serializer class for the request"""
        if self.action == "list":
            return ProjectListSerializer

        return self.serializer_class

    def perform_create(self, serializer):
        """Create a new project"""
        serializer.save(user=self.request.user)


class DocumentViewSet(viewsets.ModelViewSet):
    serializer_class = DocumentDetailSerializer
    queryset = Document.objects.all()
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Retrieve documents for current authenticated user 
        and specific project only
        """
        project_id = self.kwargs['project_pk']
        return self.queryset.filter(
            project__id=project_id,
            project__user=self.request.user
        ).order_by('-created_at')

    def get_serializer_class(self):
        """
        Return the appropriate serializer class based on the action.
        """
        if self.action == 'list':
            return DocumentListSerializer
        if self.action == 'create':
            return DocumentUploadSerializer
        return self.serializer_class

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['project'] = self.get_project()
        return context
    
    def get_project(self):
        """Get and validate the associated project"""
        project = get_object_or_404(
            Project,
            id=self.kwargs['project_pk'],
            user=self.request.user
        )
        return project

    