"""
Tests for the Chat session API endpoints
"""
from unittest.mock import patch, ANY
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
            title="Test chat session",
            project=self.project
        )
        ChatSession.objects.create(
            title="Another test chat session",
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
            title="Test chat session",
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
            title="Test chat session",
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

    @patch("chat.rag.run_rag_and_llm")
    def test_user_and_assistant_messages_are_persisted_and_returned(self, mock_run_rag):
        mock_run_rag.return_value = "AI's reply"
        chat = ChatSession.objects.create(
            title="Test chat session",
            project=self.project
        )
        payload = {
            "content":"Hello AI",
        }
        url = get_chat_messages_url(self.project.id, chat.id)
        res = self.client.post(url, payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        # Expect two messages to be returned
        self.assertIsInstance(res.data, list)
        self.assertEqual(len(res.data), 2)

        self.assertEqual(res.data[0]['content'], payload['content'])
        self.assertEqual(res.data[0]['role'], 'user')
        self.assertEqual(res.data[1]['content'], "AI's reply")
        self.assertEqual(res.data[1]['role'], "assistant")

        # Assert we actually called our RAG+LLM helper
        # with he full hisotry(system + user) and the collection name
        mock_run_rag.assert_called_once_with(
            chat.project.chroma_collection,
            [
                {"role": "system",    "content": "You are a helpful assistant."},
                {"role": "user",      "content": "Hello, AI!"}
            ]
        )

    def test_delete_chat_session(self):
        """
        Test that deleting a chat session returns a 204 status and removes the 
        session from the database.
        """
        chat = ChatSession.objects.create(
            title="Test chat session",
            project=self.project
        )
        url = get_chat_session_details_url(self.project.id, chat.id)
        res = self.client.delete(url)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(ChatSession.objects.filter(project=self.project).exists())

    def test_delete_chat_session_deletes_messages(self):
        chat = ChatSession.objects.create(
            title="Test chat session",
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
            title="Test chat session",
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
        
    