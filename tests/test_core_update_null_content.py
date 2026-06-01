import pytest
from src.swarm.core import update_null_content

def test_update_null_content_with_nulls():
    messages = [
        {"content": "Hello"},
        {"content": None},
        {"content": "World"},
        {"other": "data"},
        {"content": None}
    ]
    updated = update_null_content(messages)
    assert len(updated) == 5
    # Check messages with valid content remain unchanged.
    assert updated[0]["content"] == "Hello"
    assert updated[2]["content"] == "World"
    # Check messages with None are updated to empty strings.
    assert updated[1]["content"] == ""
    assert updated[4]["content"] == ""
    # Check that messages missing 'content' get a new key with an empty string.
    assert updated[3]["content"] == ""