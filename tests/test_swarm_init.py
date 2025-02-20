import os
import pytest
from src.swarm.core import Swarm

# Dummy OpenAI client for testing.
class DummyOpenAI:
    def __init__(self, **kwargs):
        self.kwargs = kwargs

def dummy_load_llm_config(config, model):
    return {"model": model, "api_key": "dummy-key"}

def test_swarm_init_default_model(monkeypatch):
    monkeypatch.setenv("DEFAULT_LLM", "defaultTest")
    monkeypatch.setattr("src.swarm.core.load_llm_config", dummy_load_llm_config)
    monkeypatch.setattr("src.swarm.core.OpenAI", DummyOpenAI)
    sw = Swarm(client=None, config={})
    assert sw.model == "defaultTest"
    assert sw.current_llm_config["api_key"] == "dummy-key"
    assert sw.client.kwargs["api_key"] == "dummy-key"

def test_swarm_init_with_client(monkeypatch):
    dummy_client = DummyOpenAI(api_key="existing")
    def dummy_load_llm_config_existing(config, model):
        return {"model": model, "api_key": "existing"}
    monkeypatch.setattr("src.swarm.core.load_llm_config", dummy_load_llm_config_existing)
    monkeypatch.setattr("src.swarm.core.OpenAI", DummyOpenAI)
    sw = Swarm(client=dummy_client, config={})
    assert sw.client is dummy_client