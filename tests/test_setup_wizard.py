import pytest
import json
from unittest.mock import patch, mock_open
from swarm.extensions.config.setup_wizard import run_setup_wizard

@pytest.fixture
def mock_environment():
    """Mock environment variables for API keys."""
    with patch.dict("os.environ", {"LLM_API_KEY": "mock_key"}):
        yield

@pytest.fixture
def mock_config_file():
    """Mock configuration file content."""
    return {
        "llm": {"provider": "mockai", "model": "mock-model", "temperature": 0.5},
        "mcpServers": {
            "mock-server": {"command": "mock-cmd", "args": ["--mock-arg"], "env": {"MOCK_ENV": "mock_value"}}
        },
    }

@patch("builtins.input", side_effect=["mockai", "mock-model", "0.7", "yes"])
@patch("builtins.open", new_callable=mock_open)
@patch("os.path.exists", return_value=True)
@patch("json.load", return_value={"llm": {}, "mcpServers": {}})
def test_setup_wizard_flow(mock_load, mock_exists, mock_open_file, mock_input, mock_environment):
    """Test the flow of the setup wizard."""
    config_path = "mock_config.json"
    blueprints_metadata = {"mock_blueprint": {"title": "Mock Blueprint", "description": "Mock description"}}

    updated_config = run_setup_wizard(config_path, blueprints_metadata)

    # Validate LLM settings
    assert updated_config["llm"]["provider"] == "mockai"
    assert updated_config["llm"]["model"] == "mock-model"
    assert updated_config["llm"]["temperature"] == 0.7

    # Validate configuration file save
    mock_open_file.assert_called_with(config_path, "w")
    saved_config = json.loads(mock_open_file().write.call_args[0][0])
    assert saved_config["llm"]["api_key"] == ""

@patch("os.path.exists", return_value=False)
@patch("builtins.input", side_effect=["mockai", "mock-model", "yes", "no"])
@patch("builtins.open", new_callable=mock_open)
def test_setup_wizard_no_existing_config(mock_open_file, mock_input, mock_exists, mock_environment):
    """Test setup wizard when no configuration file exists."""
    config_path = "mock_config.json"
    blueprints_metadata = {}

    updated_config = run_setup_wizard(config_path, blueprints_metadata)

    # Validate that the new config is created and saved
    assert updated_config["llm"]["provider"] == "mockai"
    mock_open_file.assert_called_with(config_path, "w")
