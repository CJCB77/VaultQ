"""
Test User endpoints
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status

USER_MODEL = get_user_model()
CREATE_USER_URL = reverse("user:create")
TOKEN_URL = reverse("user:token")

def create_user(**params):
    return USER_MODEL.objects.create_user(**params)

class PublicUserTests(TestCase):
    """Test user api public features"""

    def setUp(self):
        self.client = APIClient()
    
    def test_create_user(self):
        payload = {
            "email":"test@example.gmail",
            "password":"pass12345"
        }

        res = self.client.post(CREATE_USER_URL, payload)
        users = USER_MODEL.objects.all()

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(users), 1)

    def test_password_is_hashed(self):
        payload = {
            "email":"test@example.gmail",
            "password":"pass12345"
        }
        self.client.post(CREATE_USER_URL, payload)
        user = USER_MODEL.objects.get(email=payload['email'])

        self.assertNotEqual(user.password, payload['password'])
    
    def test_user_creation_response_structure(self):
        payload = {
            "email":"test@example.gmail",
            "password":"pass12345"
        }
        res = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(res.data.keys(), {"email"}) # type: ignore
    
    def test_email_already_exists(self):
        create_user(
            email="test@example.com",
            password="test12345"
        )
        payload = {
            "email":"test@example.gmail",
            "password":"pass12345"
        }
        res = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_password_too_short_error(self):
        payload = {
            "email":"test@example.gmail",
            "password":"pass"
        }
        res = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        # Test user was not created
        user_exists = USER_MODEL.objects.filter(email=payload['email']).exists()
        self.assertFalse(user_exists)


    def test_token_creation(self):
        payload = {
            "email":"test@example.com",
            "password":"pass12345"
        }
        create_user(**payload)
        res = self.client.post(TOKEN_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('token', res.data) # type: ignore

    def test_token_creation_wrong_email(self):
        payload = {
            "email":"test@example.com",
            "password":"pass12345"
        }
        create_user(**payload)
        res = self.client.post(TOKEN_URL, {
            'username':"user@example.com",
            'password':"pass12345"
        })

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertNotIn('token', res.data) # type: ignore
    
    def test_token_creation_wrong_password(self):
        payload = {
            "email":"test@example.com",
            "password":"pass12345"
        }
        create_user(**payload)
        res = self.client.post(TOKEN_URL, {
            'username':"test@example.com",
            'password':"djshjksh"
        })

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertNotIn('token', res.data) # type: ignore
    
    def test_token_creation_missing_fields(self):
        payload = {
            "email":"test@example.com",
            "password":"pass12345"
        }
        create_user(**payload)
        res = self.client.post(TOKEN_URL, {
            'username':"",
            'password':""
        })

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertNotIn('token', res.data) # type: ignore