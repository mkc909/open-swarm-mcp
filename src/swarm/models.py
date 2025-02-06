from django.db import models
from django.utils import timezone


class ChatConversation(models.Model):
    """Represents a single chat session."""
    conversation_id = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        app_label = "swarm"

    def __str__(self):
        return f"ChatConversation({self.conversation_id})"


class ChatMessage(models.Model):
    """Stores individual chat messages within a conversation."""
    conversation = models.ForeignKey(ChatConversation, related_name="messages", on_delete=models.CASCADE)
    sender = models.CharField(max_length=50)  # "user" or "assistant"
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"ChatMessage({self.sender}: {self.content[:30]})"
