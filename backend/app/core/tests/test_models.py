"""
Tests for models
"""
from django.test import TestCase
from django.contrib.auth import get_user_model

USER_MODEL = get_user_model()

class ModelTests(TestCase):
    """Test models"""

    def test_create_user_with_email_successful(self):
        """Test creating a user with an email is succesful"""
        email = 'test@example.com'
        password = 'testpass123'
        user = USER_MODEL.objects.create_user(
            email=email,
            password=password
        ) # type: ignore

        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(password))
    
    def test_new_user_email_normalized(self):
        """Test the email for a new user is normalized"""
        emails = [
            ['F6VH9@example.com', 'F6VH9@example.com'],
            ['m9v7R@EXAMPLE.com', 'm9v7R@example.com'],
            ['9mK9U@example.COM', '9mK9U@example.com'],
        ]

        for email, expected in emails:
            user = get_user_model().objects.create_user(email, 'sample123')
            self.assertEqual(user.email, expected)
    