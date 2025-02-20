import json
import pytest
from src.swarm.core import ChatMessage

def test_model_dump_json_removes_empty_tool_calls():
    # Create ChatMessage instance with empty tool_calls (default behavior)
    msg = ChatMessage(role="assistant", content="Test message", tool_calls=[])
    dumped = msg.model_dump_json()
    data = json.loads(dumped)
    # tool_calls key should be removed since it's an empty list
    assert "tool_calls" not in data
    # Defaults for other fields should be present
    assert data["role"] == "assistant"
    assert data["content"] == "Test message"
    # Sender default should be 'assistant' unless provided
    assert data["sender"] == "assistant"

def test_model_dump_json_preserves_tool_calls():
    # Create ChatMessage instance with non-empty tool_calls
    tool_calls_data = [{"id": "123", "function": {"name": "dummy", "arguments": "{}"}}]
    msg = ChatMessage(role="assistant", content="Another test", tool_calls=tool_calls_data)
    dumped = msg.model_dump_json()
    data = json.loads(dumped)
    # tool_calls key should be preserved since it's not empty
    assert "tool_calls" in data
    assert data["tool_calls"] == tool_calls_data
    # Validate other fields
    assert data["content"] == "Another test"
    assert data["sender"] == "assistant"