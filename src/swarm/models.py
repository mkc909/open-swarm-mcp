from django.db import models

class ChatConversation(models.Model):
    """Represents a single chat session."""
    conversation_id = models.CharField(max_length=255, primary_key=True)  # 🔄 Store conversation_id as a string
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"ChatConversation({self.conversation_id})"

class ChatMessage(models.Model):
    """Stores individual chat messages within a conversation."""
    conversation = models.ForeignKey(ChatConversation, related_name="messages", on_delete=models.CASCADE)
    sender = models.CharField(max_length=50)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    tool_call_id = models.CharField(max_length=255, blank=True, null=True)  # 🔄 Store tool_call_id as a string

    class Meta:
        ordering = ["timestamp"]
