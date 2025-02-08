from django.db import models
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from django.db.models.manager import RelatedManager

class ChatConversation(models.Model):
    """Represents a single chat session."""
    conversation_id = models.CharField(max_length=255, primary_key=True)
    created_at = models.DateTimeField(auto_now_add=True)
    # Removed redundant messages field.
    
    chat_messages: "RelatedManager[ChatMessage]"

    def __str__(self):
        return f"ChatConversation({self.conversation_id})"
    
    @property
    def messages(self):
        return self.chat_messages.all()

class ChatMessage(models.Model):
    """Stores individual chat messages within a conversation."""
    conversation = models.ForeignKey(ChatConversation, related_name="chat_messages", on_delete=models.CASCADE)
    sender = models.CharField(max_length=50)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    tool_call_id = models.CharField(max_length=255, blank=True, null=True)  # 🔄 Store tool_call_id as a string

    class Meta:
        ordering = ["timestamp"]
