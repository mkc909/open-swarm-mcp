import pytest
from src.swarm.core import filter_duplicate_system_messages

def test_filter_duplicate_system_messages_single_system():
    # When only one system message exists, it should be preserved.
    messages = [
        {"role": "system", "content": "Only system message"},
        {"role": "user", "content": "User message"}
    ]
    filtered = filter_duplicate_system_messages(messages)
    system_msgs = [msg for msg in filtered if msg["role"] == "system"]
    assert len(system_msgs) == 1
    assert system_msgs[0]["content"] == "Only system message"

def test_filter_duplicate_system_messages_multiple_systems():
    # Multiple system messages should be reduced to the first one.
    messages = [
        {"role": "system", "content": "First system message"},
        {"role": "system", "content": "Second system message"},
        {"role": "user", "content": "User message"},
        {"role": "system", "content": "Third system message"}
    ]
    filtered = filter_duplicate_system_messages(messages)
    system_msgs = [msg for msg in filtered if msg["role"] == "system"]
    assert len(system_msgs) == 1
    assert system_msgs[0]["content"] == "First system message"