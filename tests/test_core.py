import pytest
from unittest.mock import MagicMock, patch
from swarm.core import Swarm
import os
import json

@pytest.fixture
def valid_config_file(tmp_path):
    config_path = tmp_path / "swarm_config.json"
    config_content = {
        "selectedLLM": "mock_llm",
        "mcpServers": {
            "server1": {"command": "mock_command", "args": []}
        }
    }
    with open(config_path, "w") as f:
        json.dump(config_content, f)
    return str(config_path)

@pytest.fixture
def invalid_config_file(tmp_path):
    config_path = tmp_path / "swarm_config.json"
    with open(config_path, "w") as f:
        f.write("{invalid json}")
    return str(config_path)

@pytest.mark.parametrize("client, config_path", [(None, None), (MagicMock(), "custom_path")])
def test_swarm_initialization(client, config_path):
    """Test Swarm initializes with or without custom client/config."""
    swarm = Swarm(client=client, config_path=config_path)
    assert swarm.client is not None
    assert swarm.config_path == config_path or os.getcwd() + "/swarm_config.json"

def test_get_default_config_path():
    """Test the default configuration path resolution."""
    swarm = Swarm()
    default_path = swarm._get_default_config_path()
    assert default_path.endswith("swarm_config.json")

def test_load_configuration_valid(valid_config_file):
    """Test loading a valid configuration file."""
    swarm = Swarm(config_path=valid_config_file)
    config = swarm.load_configuration()
    assert config["selectedLLM"] == "mock_llm"

def test_load_configuration_missing(tmp_path):
    """Test loading a non-existent configuration file."""
    missing_path = tmp_path / "non_existent.json"
    swarm = Swarm(config_path=str(missing_path))
    config = swarm.load_configuration()
    assert config == {}

# def test_load_configuration_invalid(invalid_config_file):
#     """Test loading an invalid configuration file."""
#     swarm = Swarm(config_path=invalid_config_file)
#     with pytest.raises(json.JSONDecodeError):
#         swarm.load_configuration()

# @patch("swarm.core.validate_api_keys")
# def test_validate_api_keys(mock_validate, valid_config_file):
#     """Test API key validation."""
#     swarm = Swarm(config_path=valid_config_file)
#     swarm.validate_api_keys()
#     mock_validate.assert_called_once()
