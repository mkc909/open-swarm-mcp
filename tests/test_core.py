import os
import pytest
from unittest.mock import patch, MagicMock
from src.swarm.core import Swarm
from src.swarm.types import Agent, ChatCompletionMessage

@pytest.mark.asyncio
@patch("src.swarm.core.OpenAI")
def test_swarm_baseurl_reinit_and_dummy_key(mock_openai):
    """
    Test that Swarm reinitializes the client only when base_url changes,
    and sets a dummy API key if none is provided.
    """
    # Initial config
    config = {
        "llm": {
            "default": {
                "provider": "openai",
                "model": "gpt-3.5-turbo",
                "base_url": "https://api.openai.com/v1",
                # no api_key specified
            },
            "custom": {
                "provider": "openai",
                "model": "gpt-3.5-turbo-custom",
                "base_url": "http://localhost:11434/v1",
                # no api_key specified
            }
        }
    }

    # Instantiate Swarm
    swarm = Swarm(config=config)

    # Agent with default model (no key in config => dummy key)
    agent_default = Agent(name="DefaultAgent", model="default")

    # Call get_chat_completion once
    swarm.get_chat_completion(
        agent=agent_default,
        history=[],
        context_variables={},
        model_override=None,
        stream=False,
        debug=False
    )

    # Verify dummy key set if no SUPPRESS_DUMMY_KEY
    init_kwargs_call = mock_openai.call_args
    assert "api_key" in init_kwargs_call[1], "Should set an API key when none provided"
    assert init_kwargs_call[1]["api_key"] == "sk-DUMMYKEY", "Should be dummy key by default"

    # Reset mock to track new calls
    mock_openai.reset_mock()

    # Agent with changed base URL (should trigger reinit but same no key => dummy key)
    agent_custom = Agent(name="CustomAgent", model="custom")
    swarm.get_chat_completion(
        agent=agent_custom,
        history=[],
        context_variables={},
        model_override=None,
        stream=False,
        debug=False
    )

    # Verify reinit occurred with new base_url
    reinit_kwargs_call = mock_openai.call_args
    assert reinit_kwargs_call is not None, "OpenAI should be reinitialized due to base_url change"
    assert "api_key" in reinit_kwargs_call[1], "Should still have an API key set"
    assert reinit_kwargs_call[1]["api_key"] == "sk-DUMMYKEY", "Still dummy key"

    # Now call again with the same base_url => no reinit
    mock_openai.reset_mock()
    swarm.get_chat_completion(
        agent=agent_custom,
        history=[],
        context_variables={},
        model_override=None,
        stream=False,
        debug=False
    )
    assert not mock_openai.called, "OpenAI should not reinitialize if base_url hasn't changed"