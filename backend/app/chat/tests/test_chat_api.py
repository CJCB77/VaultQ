"""
Tests for the Chat session API endpoints
"""
from unittest.mock import patch, MagicMock
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

def get_chat_session_details_url(project_id, chat_id):
    return reverse(
        "chat:chat-detail",
        args=[project_id, chat_id]
    )

def get_chat_messages_url(project_id, chat_id):
    return reverse(
        "chat:chat-messages",
        args=[project_id, chat_id]
    )

def get_chat_session_rename_url(project_id,chat_id):
     return reverse(
        "chat:chat-rename",
        args=[project_id, chat_id]
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
        serializer = ChatSessionSerializer(sessions, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(serializer.data, res.data)

    def test_get_project_only_chats(self):
        new_project = Project.objects.create(
            name="Another test project",
            description="description",
            user=self.user
        )
        ChatSession.objects.create(
            title="Test chat session",
            project=self.project
        )
        ChatSession.objects.create(
            title="Another test chat session",
            project=new_project
        )
        url = get_chat_session_project_url(self.project.id)
        res = self.client.get(url)

        sessions = ChatSession.objects.filter(project=self.project)
        serializer = ChatSessionSerializer(sessions, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(sessions), 1)
        self.assertEqual(serializer.data, res.data)

    def test_create_new_chat_session(self):
        payload = {
            "title": "Testing chat...",
            "project":self.project
        }
        url = get_chat_session_project_url(self.project.id)
        res = self.client.post(url, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertTrue(ChatSession.objects.filter(project=self.project).exists())

    def test_get_chat_session_metadata(self):
        chat = ChatSession.objects.create(
            title="Test chat session"
            project=self.project
        )
        url = get_chat_session_details_url(self.project.id, chat.id)
        res = self.client.get(url)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        chatSession = chatSession.objects.get(pk=res.data['id'])
        serializer = ChatSessionSerializer(chatSession)

        self.assertEqual(res.data, serializer.data)
        
    def test_get_chat_session_messages(self):
        chat = ChatSession.objects.create(
            title="Test chat session"
            project=self.project
        )
        ChatMessage.objects.bulk_create([
            ChatMessage(
                session=chat,
                role=ChatMessage.SESSION_ROLES.SYSTEM,
                content="You are a useful assitant that helps answering questions."
            ),
            ChatMessage(
                session=chat,
                role=ChatMessage.SESSION_ROLES.USER,
                content="Which is the largest building in the world?"
            )
        ])
        
        url = get_chat_messages_url(self.project.id, chat.id)
        res = self.client.get(url)

        messages = ChatMessages.objects.filter(session=chat).order_by('created_at')
        serializer = ChatMessageSerializer(messages, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)
        
        self.assertEqual(len(res.data), 2)
        self.assertEqual(res.data[0]['id'], system_message.id)
        self.assertEqual(res.data[1]['id'], user_message.id)
        self.assertEqual(res.data[0]['role'], ChatMessage.SESSION_ROLES.SYSTEM)



    def test_sent_message_is_stored(self):
        chat = ChatSession.objects.create(
            title="Test chat session"
            project=self.project
        )
        payload = {
            "session":chat,
            "content":"Test message",
            "role": ChatMessage.SESSION_ROLES.USER
        }
        url = get_chat_session_details_url(self.project.id, chat.id)
        res = self.client.post(url, payload)
        message = ChatMessage.objects.filter(session=chat)
        serializer = ChatMessageSerializer(message)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(serializer.data, res.data)
        
    def test_delete_chat_session(self):
        chat = ChatSession.objects.create(
            title="Test chat session"
            project=self.project
        )
        url = get_chat_session_details_url(self.project.id, chat.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(ChatSession.objects.filter(project=self.project).exists())

    def test_delete_chat_session_deletes_messages(self):
        chat = ChatSession.objects.create(
            title="Test chat session"
            project=self.project
        )
        ChatMessage.objects.bulk_create([
            ChatMessage(
                session=chat,
                role=ChatMessage.SESSION_ROLES.SYSTEM,
                content="You are a useful assitant that helps answering questions."
            ),
            ChatMessage(
                session=chat,
                role=ChatMessage.SESSION_ROLES.USER,
                content="Which is the largest building in the world?"
            )
        ])

        url = get_chat_session_details_url(self.project.id, chat.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(ChatMessage.objects.filter(session=chat).exists())

    def test_update_chat_session_title(self):
        chat = ChatSession.objects.create(
            title="Test chat session"
            project=self.project
        )
        payload = {
            "title":"Another title"
        }
        url = get_chat_session_rename_url(self.project.id, chat.id)
        res = self.client.patch(url, payload)
        chat.refresh_from_db()


        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(chat.title, payload['title'])
        
    