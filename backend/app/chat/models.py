"""
Chat models for user querying RAG
"""
from django.db import models
from django.utils import timezone

class ChatSession(models.Model):
    """
    A class representing a chat session of a project
    """
    title = models.CharField(max_length=255)
    project = models.ForeignKey(
        'Project', 
        on_delete=models.CASCADE,
        help_text="The associated project"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        # On first save, if no tile, got ot a default
        if not self.pk and not self.title:
            self.title = f"New chat {timezone.now():%Y-%m-%d %H:%M}"
            super().save(*args, **kwargs)


class ChatMessage(models.Model):
    """
    A class representing a chat message sent by the user or AI
    """
    class ChatRoles(models.TextChoices):
        SYSTEM = ("system", "System")
        USER = ("user", "User")
        ASSISTANT = ("assistant", "Assistant")
    
    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE)
    role = models.CharField(choices=ChatRoles, max_length=20)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]
        