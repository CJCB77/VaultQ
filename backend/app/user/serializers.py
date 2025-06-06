"""
Serializers for the User API View
"""
from django.contrib.auth import (
    get_user_model,
    authenticate
)
from django.contrib.auth.password_validation import validate_password
from django.utils.translation import gettext_lazy as _

from rest_framework import serializers

USER_MODEL = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """Serializer for the user object"""

    class Meta:
        model = USER_MODEL
        fields = ['email','password','first_name','last_name']
        extra_kwargs = {
            'password': {'write_only': True, 'validators':[validate_password]},
        }
    
    def create(self, validated_data):
        return USER_MODEL.objects.create_user(**validated_data)

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        user = super().update(instance, validated_data)

        if password:
            user.set_password(password)
            user.save()
        
        return user


class AuthTokenSerializer(serializers.Serializer):
    """Serializer for the user authentication token"""
    email = serializers.EmailField() # Validates email format automatically
    password = serializers.CharField(
        style={'input_type': 'password'}, 
        trim_whitespace=False 
    )

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')
        user = authenticate(
            request=self.context.get('request'),
            username=email,
            password=password
        )

        if not user:
            msg = _('Unable to authenticate with provided credentials')
            raise serializers.ValidationError(msg, code='authentication')
        
        attrs['user'] = user
        return attrs