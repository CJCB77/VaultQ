"""
Tests for the Chat session API endpoints
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status

from project.models import Project

User = get_user_model()


def get_chat_session_project_url(project_id):
    return reverse(
        "chat:chat-list",
        args=[project_id]
    )

class PublicChatApiTests(TestCase):
    """Class to test open Chat API endpoints"""
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="test@example.com",
            password="pass12345"
        )
        self.project = Project.objects.create(
            name="Test",
            description="description",
            user=self.user
        )
    
    def test_needs_authentication(self):
        """
        Test that authentication is required to access the chat session API
        """
        url = get_chat_session_project_url(self.project.id)
        res = self.client.get(url)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateChatApiTests(TestCase):
    """
    Class for testing Chat API functionalities
    """

    def setUp(self):
        self.user = User.objects.create_user(
            email="test@example.com",
            password="pass12345"
        )
        self.project = Project.objects.create(
            name="Test",
            description="description",
            user=self.user
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
    
    def test_get_project_chats(self):
        ChatSession.objects.create(
            title="Test chat session"
            project=self.project
        )
        ChatSession.objects.create(
            title="Another test chat session"
            project=self.project
        )
        url = get_chat_session_project_url(self.project.id)
        res = self.client.get(url)

        sessions = ChatSession.objects.all().order_by("-id")
        serializer = ChatSessionSerializer(sessions)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(serializer.data, res.data)

    def test_get_project_only_chats(self):
        new_project = Project.objects.create(
            name="Another test project",
            description="description",
            user=self.user
        )
        ChatSession.objects.create(
            title="Test chat session"
            project=self.project
        )
        ChatSession.objects.create(
            title="Another test chat session"
            project=new_project
        )
        url = get_chat_session_project_url(self.project.id)
        res = self.client.get(url)

        sessions = ChatSession.objects.filter(project=self.project)
        serializer = ChatSessionSerializer(sessions)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(sessions), 1)
        self.assertEqual(serializer.data, res.data)

    def test_create_new_chat_session(self):
        pass

    def test_get_chat_session_metadata(self):
        pass

    def test_get_chat_session_messages(self):
        pass

    def test_sent_message_is_stored(self):
        pass

    def test_send_new_message_invokes_rag_and_llm(self):
        pass

    def test_delete_chat_session(self):
        pass

    def test_delete_chat_session_deletes_messages(self):
        pass

    def test_update_chat_session_title(self):
        pass

    def test_get_project_active_chat_session(self):
        pass

    def test_chat_created_with_default_system_message(self):
        pass

    