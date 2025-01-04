import pytest
import json
from unittest.mock import patch, mock_open
from swarm.extensions.config.setup_wizard import run_setup_wizard


@pytest.fixture
def mock_environment():
    """
    Mock environment variables for API keys.

    Ensures that API keys are available for tests that require them, 
    without affecting the actual system environment.
    """
    with patch.dict("os.environ", {"LLM_API_KEY": "mock_key"}):
        yield


@pytest.fixture
def mock_config_file():
    """
    Mock configuration file content matching `swarm_config.json`.

    Simulates an existing configuration for testing the `run_setup_wizard` function.
    """
    return {
        "llm": {
            "provider": "ollama",
            "model": "mock-model",
            "temperature": 0.5,
            "api_key": "mock_key",
        },
        "mcpServers": {
            "mock-server": {
                "command": "mock-cmd",
                "args": ["--mock-arg"],
                "env": {"MOCK_ENV": "mock_value"},
            }
        },
        "blueprints": {
            "mock_blueprint": {
                "title": "Mock Blueprint",
                "description": "Mock description",
            }
        },
    }


# @patch("builtins.input", side_effect=["ollama", "mock-model", "0.7", "0"])
# @patch("builtins.open", new_callable=mock_open)
# @patch("os.path.exists", return_value=True)
# def test_setup_wizard_flow(mock_exists, mock_open_file, mock_input, mock_environment, mock_config_file):
#     """
#     Test the flow of the setup wizard when a configuration file already exists.

#     Validates that:
#     - Existing configuration is loaded correctly.
#     - LLM settings and blueprints are configured as expected.
#     - Configuration is saved correctly to a file.
#     """
#     config_path = "mock_config.json"
#     blueprints_metadata = {
#         "mock_blueprint": {
#             "title": "Mock Blueprint",
#             "description": "Mock description",
#         }
#     }

#     # Mock `json.load` to return the mock_config_file content
#     with patch("json.load", return_value=mock_config_file):
#         updated_config = run_setup_wizard(config_path, blueprints_metadata)

#     # Validate LLM settings
#     assert updated_config["llm"]["provider"] == "ollama", "LLM provider should be 'ollama'."
#     assert updated_config["llm"]["model"] == "mock-model", "LLM model should match user input."
#     assert updated_config["llm"]["temperature"] == 0.7, "Temperature should match user input."

#     # Validate configuration file save
#     mock_open_file.assert_called_with(config_path, "w")
#     saved_config = json.loads(mock_open_file().write.call_args[0][0])
#     assert saved_config["llm"]["api_key"] == "mock_key", "API key should be saved correctly."


# @patch("os.path.exists", return_value=False)
# @patch("builtins.input", side_effect=["ollama", "mock-model", "0.7", "0"])
# @patch("builtins.open", new_callable=mock_open)
# def test_setup_wizard_no_existing_config(mock_open_file, mock_input, mock_exists, mock_environment):
#     """
#     Test the setup wizard when no configuration file exists.

#     Validates that:
#     - LLM settings and blueprints are configured from scratch.
#     - Configuration is saved correctly to a new file.
#     """
#     config_path = "mock_config.json"
#     blueprints_metadata = {
#         "mock_blueprint": {
#             "title": "Mock Blueprint",
#             "description": "Mock description",
#         }
#     }

#     updated_config = run_setup_wizard(config_path, blueprints_metadata)

#     # Validate LLM settings
#     assert updated_config["llm"]["provider"] == "ollama", "LLM provider should be 'ollama'."
#     assert updated_config["llm"]["model"] == "mock-model", "LLM model should match user input."
#     assert updated_config["llm"]["temperature"] == 0.7, "Temperature should match user input."

#     # Validate configuration file save
#     mock_open_file.assert_called_with(config_path, "w")
#     saved_config = json.loads(mock_open_file().write.call_args[0][0])
#     assert saved_config["llm"]["api_key"] == "mock_key", "API key should be saved correctly."
