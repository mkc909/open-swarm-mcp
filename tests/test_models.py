import pytest
from django.utils import timezone
from swarm.models import ChatConversation, ChatMessage

@pytest.mark.django_db
def test_create_chat_conversation():
    """Ensure a new ChatConversation can be created with an ID."""
    conversation = ChatConversation.objects.create(conversation_id="test123")
    assert conversation.conversation_id == "test123"
    assert ChatConversation.objects.count() == 1

@pytest.mark.django_db
def test_add_message_to_conversation():
    """Verify that ChatMessage can be linked to a conversation."""
    conversation = ChatConversation.objects.create(conversation_id="test123")
    message = ChatMessage.objects.create(
        conversation=conversation,
        sender="user",
        content="Hello, world!",
        timestamp=timezone.now()
    )
    assert message in conversation.messages.all()
    assert ChatMessage.objects.count() == 1

@pytest.mark.django_db
def test_message_ordering():
    """Ensure messages are ordered correctly by timestamp."""
    conversation = ChatConversation.objects.create(conversation_id="test123")
    ChatMessage.objects.create(conversation=conversation, sender="user", content="First", timestamp=timezone.now())
    ChatMessage.objects.create(conversation=conversation, sender="assistant", content="Second", timestamp=timezone.now())

    messages = list(conversation.messages.all().order_by("timestamp"))
    assert messages[0].content == "First"
    assert messages[1].content == "Second"

@pytest.mark.django_db
def test_retrieve_chat_history():
    """Fetch conversation history and verify its integrity."""
    conversation = ChatConversation.objects.create(conversation_id="test123")
    ChatMessage.objects.create(conversation=conversation, sender="user", content="Message 1", timestamp=timezone.now())
    ChatMessage.objects.create(conversation=conversation, sender="assistant", content="Message 2", timestamp=timezone.now())

    retrieved_conversation = ChatConversation.objects.get(conversation_id="test123")
    messages = retrieved_conversation.messages.all()
    assert len(messages) == 2
    assert messages[0].sender == "user"
    assert messages[1].sender == "assistant"

@pytest.mark.django_db
def test_cascade_delete_conversation():
    """Ensure deleting a conversation deletes all related messages."""
    conversation = ChatConversation.objects.create(conversation_id="test123")
    ChatMessage.objects.create(conversation=conversation, sender="user", content="Hello", timestamp=timezone.now())

    assert ChatMessage.objects.count() == 1
    conversation.delete()
    assert ChatMessage.objects.count() == 0  # Messages should be deleted with the conversation
