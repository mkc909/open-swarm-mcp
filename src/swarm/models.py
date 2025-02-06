from django.db import models
import uuid
from django.utils import timezone

class ChatConversation(models.Model):
    """Represents a single chat session."""
    conversation_id = models.UUIDField(default=uuid.uuid4, primary_key=True) 
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        app_label = "swarm"

    def __str__(self):
        return f"ChatConversation({self.conversation_id})"

    def add_message(self, sender, content):
        """Helper method to add a message to the conversation."""
        ChatMessage.objects.create(conversation=self, sender=sender, content=content)

    def get_messages(self):
        """Retrieve all messages in this conversation."""
        return self.messages.order_by("timestamp")


class ChatMessage(models.Model):
    """Stores individual chat messages within a conversation."""
    conversation = models.ForeignKey(ChatConversation, related_name="messages", on_delete=models.CASCADE)
    sender = models.CharField(max_length=50)  # "user" or "assistant"
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["timestamp"]  # Ensures chronological order

    def __str__(self):
        return f"ChatMessage({self.sender}: {self.content[:30]})"
