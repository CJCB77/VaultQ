"""
Serializers for the Project API View
"""
from rest_framework import serializers
from models import Project


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
    