import pytest
import datetime
from src.swarm.core import filter_messages, serialize_datetime

def test_filter_messages_excludes_null():
    messages = [
        {"content": "Hello"},
        {"content": None},
        {"content": "World"},
        {"no_content": "data"},
        {"content": ""}
    ]
    filtered = filter_messages(messages)
    expected = [
        {"content": "Hello"},
        {"content": "World"},
        {"content": ""}
    ]
    assert filtered == expected

def test_serialize_datetime_success():
    dt = datetime.datetime(2025, 2, 20, 19, 48)
    result = serialize_datetime(dt)
    assert result == dt.isoformat()

def test_serialize_datetime_failure():
    with pytest.raises(TypeError):
        serialize_datetime("not a datetime")