import os
import pytest
from src.swarm.core import truncate_message_history

# Dummy encoding to simulate token encoding; splits text by whitespace.
class DummyEncoding:
    def encode(self, text):
        # Return list of words as tokens; if text is empty, return empty list.
        if not text:
            return []
        return text.split()

# Dummy functions to override tiktoken behavior.
def dummy_encoding_for_model(model):
    return DummyEncoding()

def dummy_get_encoding(encoding_name):
    return DummyEncoding()

@pytest.fixture(autouse=True)
def patch_tiktoken(monkeypatch):
    # Patch tiktoken.encoding_for_model and tiktoken.get_encoding to use DummyEncoding.
    import tiktoken
    monkeypatch.setattr(tiktoken, "encoding_for_model", dummy_encoding_for_model)
    monkeypatch.setattr(tiktoken, "get_encoding", dummy_get_encoding)

def test_truncate_message_history_no_truncation(monkeypatch):
    # Test case where truncation is not needed.
    messages = [
        {"content": "hello world"},           # 2 tokens
        {"content": "this is a test"},          # 4 tokens
    ]
    # Total tokens = 2 + 4 = 6, max_tokens = 10, so no truncation happens.
    result = truncate_message_history(messages.copy(), model="dummy-model", max_tokens=10)
    # The result should remain intact.
    assert result == messages

def test_truncate_message_history_with_truncation(monkeypatch):
    # Test case where messages need to be removed.
    messages = [
        {"content": "hello world"},           # 2 tokens
        {"content": "this is a longer test"},   # 5 tokens
        {"content": "another message here"},    # 3 tokens
    ]
    # Total tokens = 2+5+3 = 10. Set max_tokens to 7. 
    # The loop should remove messages from the front until token count <= 7.
    # Removing first message (2 tokens) -> remaining tokens = 5+3 = 8 (still >7)
    # Removing next message (5 tokens) -> remaining tokens = 3 <=7.
    result = truncate_message_history(messages.copy(), model="dummy-model", max_tokens=7)
    # Expected result should only include the last message.
    expected = [
        {"content": "another message here"}
    ]
    assert result == expected

def test_truncate_message_history_with_env_variable(monkeypatch):
    # Test truncation when max_tokens is not provided and MAX_OUTPUT env variable is set.
    os.environ["MAX_OUTPUT"] = "4"
    messages = [
        {"content": "one two three"},    # 3 tokens
        {"content": "four five six seven"}, # 4 tokens
    ]
    # Total tokens = 3 + 4 = 7, max_tokens = 4 so first message removed, remaining tokens = 4 which meets exactly.
    result = truncate_message_history(messages.copy(), model="dummy-model")
    expected = [
        {"content": "four five six seven"}
    ]
    assert result == expected
    del os.environ["MAX_OUTPUT"]