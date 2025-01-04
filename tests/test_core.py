# tests/test_core.py

import pytest
import os
import json
from unittest.mock import patch, Mock
from swarm.core import Swarm
from swarm.types import Agent, Tool, Result
import openai  # Import openai to fix NameError

# Helper function to create a mock response
def mock_chat_completion_create(**kwargs):
    mock_response = Mock()
    mock_response.choices = [
        Mock(
            message=Mock(
                role="assistant",
                content="This is a mocked response.",
                model_dump_json=lambda: json.dumps({
                    "role": "assistant",
                    "content": "This is a mocked response."
                })
            )
        )
    ]
    return mock_response

# Fixture to create a sample configuration
@pytest.fixture
def sample_config(tmp_path):
    config = {
        "llm": {
            "default": {
                "provider": "openai",
                "model": "gpt-4o",
                "base_url": "https://api.openai.com/v1",
                "api_key": "${OPENAI_API_KEY}",
                "temperature": 0.7
            },
            "openai": {
                "provider": "openai",
                "model": "gpt-4o",
                "base_url": "https://api.openai.com/v1",
                "api_key": "${OPENAI_API_KEY}",
                "temperature": 0.7
            },
            "grok": {
                "provider": "openai",
                "model": "grok-2-1212",
                "base_url": "https://api.x.ai/v1",
                "api_key": "${XAI_API_KEY}",
                "temperature": 0.0
            },
            "ollama": {
                "provider": "openai",
                "model": "llama3.2:latest",
                "base_url": "http://localhost:11434/",
                "api_key": "",
                "temperature": 0.0
            }
        },
        "mcpServers": {
            "brave-search": {
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-brave-search"],
                "env": {
                    "BRAVE_API_KEY": "${BRAVE_API_KEY}"
                }
            },
            "sqlite": {
                "command": "npx",
                "args": ["-y", "mcp-server-sqlite-npx", "${SQLITE_DB_PATH}"],
                "env": {
                    "npm_config_registry": "https://registry.npmjs.org",
                    "SQLITE_DB_PATH": "${SQLITE_DB_PATH}"
                }
            },
            "sqlite-uvx": {
                "command": "uvx",
                "args": ["mcp-server-sqlite", "--db-path", "/tmp/test.db"]
            },
            "everything": {
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-everything"],
                "env": {}
            },
            "filesystem": {
                "command": "npx",
                "args": [
                    "-y",
                    "@modelcontextprotocol/server-filesystem",
                    "$ALLOWED_PATHS"
                ],
                "env": {
                    "ALLOWED_PATHS": "${ALLOWED_PATHS}"
                }
            }
        }
    }

    config_file = tmp_path / "swarm_settings.json"
    with open(config_file, "w") as f:
        json.dump(config, f)

    return str(config_file)

# Fixture to set environment variables
@pytest.fixture
def set_env_vars(monkeypatch):
    env_vars = {
        "LLM": "grok",
        "XAI_API_KEY": "test_grok_api_key",
        "OPENAI_API_KEY": "test_openai_api_key",
        "BRAVE_API_KEY": "test_brave_api_key",
        "SQLITE_DB_PATH": "/tmp/test.db",
        "ALLOWED_PATHS": "/allowed/path",
    }
    for key, value in env_vars.items():
        monkeypatch.setenv(key, value)

# # Test to validate API keys
# def test_validate_api_keys(sample_config, set_env_vars):
#     """
#     Test that validate_api_keys correctly sets the API key from environment variables.
#     """
#     with patch('openai.ChatCompletion.create', side_effect=mock_chat_completion_create) as mock_create:
#         swarm = Swarm(config_path=sample_config)

#         # Initialize with an agent that uses 'grok' LLM
#         agent = Agent(
#             name="TestAgent",
#             model="grok-2-1212",
#             instructions="You are a test agent.",
#             functions=[],
#             tool_choice=None,
#             parallel_tool_calls=True,
#             mcp_servers=[],
#             env_vars={}
#         )

#         # Run a simple chat completion
#         response = swarm.run(agent=agent, messages=[], stream=False)

#         # Verify that the OpenAI client was called with correct parameters
#         mock_create.assert_called_once()
#         args, kwargs = mock_create.call_args

#         # Check that the base_url was set correctly
#         assert openai.base_url == "https://api.x.ai/v1", "API base URL does not match config."

#         # Check that the api_key was set correctly
#         assert openai.api_key == "test_grok_api_key", "API key does not match config."

# # Test to ensure that core.py uses LLM config from JSON
# def test_llm_config_usage(sample_config, set_env_vars):
#     """
#     Test that core.py correctly uses the LLM configuration from the JSON config file.
#     """
#     with patch('openai.ChatCompletion.create', side_effect=mock_chat_completion_create) as mock_create:
#         swarm = Swarm(config_path=sample_config)

#         # Verify that the OpenAI client is configured correctly
#         selected_llm = os.getenv("LLM")
#         llm_config = {
#             "provider": "openai",
#             "model": "grok-2-1212",
#             "base_url": "https://api.x.ai/v1",
#             "api_key": "test_grok_api_key",
#             "temperature": 0.0
#         }

#         assert openai.base_url == llm_config["base_url"], "API base URL does not match config."
#         assert openai.api_key == llm_config["api_key"], "API key does not match config."

#         # Initialize with an agent that uses 'grok' LLM
#         agent = Agent(
#             name="TestAgent",
#             model="grok-2-1212",
#             instructions="You are a test agent.",
#             functions=[],
#             tool_choice=None,
#             parallel_tool_calls=True,
#             mcp_servers=[],
#             env_vars={}
#         )

#         # Run a simple chat completion
#         response = swarm.run(agent=agent, messages=[], stream=False)

#         # Verify that the OpenAI client was called with correct parameters
#         mock_create.assert_called_once()
#         args, kwargs = mock_create.call_args

#         # Check the parameters passed to OpenAI
#         assert kwargs["model"] == "grok-2-1212", "Model does not match config."
#         assert kwargs["temperature"] == 0.0, "Temperature does not match config."

def test_load_configuration_invalid():
    """
    Test Swarm initialization with an invalid configuration dictionary.
    """
    # Mock configuration to simulate invalid data
    invalid_config = None  # Simulate missing or invalid config

    # Initialize Swarm and ensure defaults are used
    swarm = Swarm(config=invalid_config)

    assert swarm.model == "gpt-4o", "Default model should be set when no config is provided."
    assert swarm.temperature == 0.7, "Default temperature should be set when no config is provided."
    assert swarm.tool_choice == "sequential", "Default tool_choice should be set when no config is provided."
    assert not swarm.parallel_tool_calls, "Default parallel_tool_calls should be False when no config is provided."
