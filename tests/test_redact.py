import os
import pytest
from src.swarm.utils.redact import redact_sensitive_data

@pytest.fixture(autouse=True)
def setup_env(monkeypatch):
    # Set up environment variables for testing so that "secretvalue" is considered sensitive.
    monkeypatch.setenv("TEST_API_KEY", "secretvalue")

def test_redact_sensitive_key_in_dict(monkeypatch):
    data = {"api_key": "secretvalue", "other": "value"}
    result = redact_sensitive_data(data, reveal_chars=3, mask="***")
    expected_value = "sec***lue"
    assert result["api_key"] == expected_value
    assert result["other"] == "value"

def test_no_redaction_for_non_sensitive_key(monkeypatch):
    data = {"username": "secretvalue"}
    result = redact_sensitive_data(data, reveal_chars=3, mask="***")
    assert result["username"] == "secretvalue"

def test_redact_in_nested_structure(monkeypatch):
    data = {"outer": {"token": "secretvalue", "info": "data"}, "list": [{"api_key": "secretvalue"}, "nochange"]}
    result = redact_sensitive_data(data, reveal_chars=2, mask="--")
    expected_token = "se--ue"
    expected_api_key = "se--ue"
    assert result["outer"]["token"] == expected_token
    assert result["list"][0]["api_key"] == expected_api_key
    assert result["outer"]["info"] == "data"
    assert result["list"][1] == "nochange"

def test_list_input(monkeypatch):
    data = ["secretvalue", "nonsense"]
    result = redact_sensitive_data(data, reveal_chars=2, mask="xx")
    expected = ["sexxue", "nonsense"]
    assert result == expected

def test_short_string(monkeypatch):
    short_value = "short"
    monkeypatch.setenv("SHORT", short_value)
    data = {"api_key": short_value}
    result = redact_sensitive_data(data, reveal_chars=3, mask="###")
    assert result["api_key"] == "###"