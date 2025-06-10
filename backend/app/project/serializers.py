"""
Serializers for the Project API View
"""
from rest_framework import serializers
from .models import (
    Project,
    Document
)
from django.urls import reverse

class DocumentUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = ['file']
        read_only_fields = ['file_size', 'name', 'content_type']
        extra_kwargs = {'file': {'write_only':True}}
    
    def create(self, validated_data):
        request = self.context['request']
        project = self.context['project']
        uploaded_file = validated_data['file']
        if request is None or project is None:
            raise serializers.ValidationError("Missing request or project context.")
        
        doc = Document(
            project=project,
            uploaded_by = request.user,
            name=uploaded_file.name,
            file = uploaded_file,
            file_size = uploaded_file.size,
            content_type = getattr(uploaded_file, 'content_type', 'application/octet-stream')
        )
        doc.save()
        return doc


class DocumentListSerializer(serializers.ModelSerializer):
    """Serializer for listing documents"""
    class Meta:
        model = Document
        fields = ['id', 'name', 'processing_status', 'content_type']


class DocumentDetailSerializer(serializers.ModelSerializer):
    download_url = serializers.SerializerMethodField()

    class Meta:
        model = Document
        fields = [
            'id', 'name', 'processing_status', 'chunks_count', 'content_type', 
            'file', 'file_size','uploaded_by','uploaded_at', 'download_url',
            'uploaded_by'
        ]
        read_only_fields = fields 
    
    def get_download_url(self, obj):
        """Get the reverse URL to my 'download' action"""
        request = self.context.get('request')
        return request.build_absolute_uri(
            reverse('projects:project-documents-download', 
                    args=[obj.project.id, obj.id])
        )

class ProjectListSerializer(serializers.ModelSerializer):
    """Project Serializer for list endpoint"""
    class Meta:
        model = Project
        fields = ['id', 'name', 'created_at']
        read_only_fields = ['id', 'created_at']


class ProjectDetailSerializer(serializers.ModelSerializer):
    """Project Serializer for details endpoint"""
    class Meta:
        model = Project
        fields = [
            'id',
            'name',
            'description',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id','created_at','updated_at']
    