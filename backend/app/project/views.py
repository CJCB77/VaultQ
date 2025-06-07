"""
API Views for the Project model
"""

from .models import Project
from .serializers import (
    ProjectListSerializer,
    ProjectDetailSerializer,
)

from rest_framework import (
    viewsets,
)
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
