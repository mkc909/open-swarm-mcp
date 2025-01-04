import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from swarm.core import Swarm
from swarm.types import Agent, Function, ChatCompletionMessageToolCall, Response, Result
import os
import json


@pytest.fixture
def valid_config_file(tmp_path):
    """Fixture for creating a valid configuration file."""
    config_path = tmp_path / "swarm_config.json"
    config_content = {
        "selectedLLM": "mock_llm",
        "llm": {
            "mock_llm": {
                "api_key": "${MOCK_API_KEY}"
            }
        },
        "mcpServers": {
            "server1": {"command": "mock_command", "args": []}
        }
    }
    with open(config_path, "w") as f:
        json.dump(config_content, f)
    return str(config_path)


@pytest.fixture
def invalid_config_file(tmp_path):
    """Fixture for creating an invalid configuration file."""
    config_path = tmp_path / "swarm_config.json"
    with open(config_path, "w") as f:
        f.write("{invalid json}")
    return str(config_path)


def test_load_configuration_invalid(invalid_config_file):
    """Test loading an invalid configuration file gracefully."""
    swarm = Swarm(config_path=invalid_config_file)
    assert swarm.config == {}, "Invalid JSON should result in an empty config."


@patch("swarm.core.os.getenv")
def test_validate_api_keys(mock_getenv, valid_config_file):
    """Test API key validation with mocked environment variables."""
    # The api_key in config is "${MOCK_API_KEY}", so getenv should be called with "MOCK_API_KEY"
    mock_getenv.return_value = "mock_api_key_value"
    swarm = Swarm(config_path=valid_config_file)
    mock_getenv.assert_called_once_with("MOCK_API_KEY")


# @patch("swarm.core.MCPClientManager")
# @patch("swarm.core.OpenAI")
# @patch("swarm.core.os.getenv")
# def test_run_initialization(mock_getenv, mock_openai, mock_mcp_client_manager, valid_config_file):
#     """Test that the run method initializes correctly."""
#     # Mock the environment variable
#     mock_getenv.return_value = "mock_api_key_value"

#     # Mock the OpenAI client
#     mock_chat_completion = MagicMock()
#     mock_chat_completion.create.return_value = MagicMock(
#         choices=[MagicMock(message=MagicMock(role="assistant", content="Mocked assistant response"))]
#     )
#     mock_openai.return_value.chat.completions = mock_chat_completion

#     # Mock the MCPClientManager instance and its initialize_and_list_tools method
#     mock_mcp_instance = MagicMock()
#     mock_mcp_instance.initialize_and_list_tools = AsyncMock(return_value=[{"id": 2, "result": {"tools": []}}])
#     mock_mcp_client_manager.return_value = mock_mcp_instance

#     swarm = Swarm(config_path=valid_config_file)

#     # Create a mock agent
#     mock_agent = Agent(
#         name="TestAgent",
#         functions=[],
#         model="mock-model",
#         instructions="Test instructions",
#         mcp_servers=["server1"],
#         env_vars={},
#         tool_choice=None,
#         parallel_tool_calls=False
#     )
#     messages = [{"role": "user", "content": "Test"}]

#     # Run the swarm
#     response = swarm.run(agent=mock_agent, messages=messages)

#     # Assertions
#     assert response is not None, "Run should not return None"
#     assert isinstance(response, Response), "Response should be an instance of Response"
#     # Ensure MCPClientManager was instantiated with correct parameters
#     mock_mcp_client_manager.assert_called_once_with(command="mock_command", args=[], env={}, timeout=30)
#     # Ensure initialize_and_list_tools was called
#     mock_mcp_instance.initialize_and_list_tools.assert_called_once()
#     # Ensure OpenAI chat completion was called with expected parameters
#     mock_chat_completion.create.assert_called_once_with(
#         model='mock-model',
#         messages=[{'role': 'system', 'content': 'Test instructions'}, {'role': 'user', 'content': 'Test'}],
#         tools=None,
#         tool_choice=None,
#         stream=False
#     )


@patch("swarm.core.OpenAI")
@patch("swarm.core.os.getenv")
def test_wrap_mcp_tool(mock_getenv, mock_openai, valid_config_file):
    """Test wrapping an MCP tool call."""
    # Mock the environment variable
    mock_getenv.return_value = "mock_api_key_value"

    # Mock the OpenAI client (though it's not used in this test)
    mock_chat_completion = MagicMock()
    mock_chat_completion.create.return_value = MagicMock(
        choices=[MagicMock(message=MagicMock(role="assistant", content="Mocked assistant response"))]
    )
    mock_openai.return_value.chat.completions = mock_chat_completion

    # Instantiate Swarm
    swarm = Swarm(config_path=valid_config_file)

    # Create a mock MCPClientManager with a call_tool method
    mock_mcp_client = MagicMock()
    mock_mcp_client.call_tool = AsyncMock(return_value={"result": {"content": [{"text": "mock result"}]}})
    swarm.mcp_clients = {"server1": mock_mcp_client}

    # Wrap the tool and call it
    wrapped_tool = swarm._wrap_mcp_tool("server1", "mock_tool", desc="Mock tool description")
    result = wrapped_tool(arg1="value1")

    # The call_tool should be called with tool_name and kwargs
    mock_mcp_client.call_tool.assert_called_once_with("mock_tool", {"arg1": "value1"})
    assert result == "mock result", "Wrapped tool function did not return expected result"
