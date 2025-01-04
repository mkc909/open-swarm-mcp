import pytest
from unittest.mock import patch, mock_open
from swarm.extensions.config.config_loader import (
    resolve_placeholders,
    load_server_config,
    validate_api_keys,
    are_required_mcp_servers_running,
)

@pytest.fixture
def mock_env():
    """Mock environment variables."""
    with patch.dict("os.environ", {"TEST_VAR": "test_value"}):
        yield

@pytest.fixture
def valid_config():
    """Provide a valid configuration dictionary."""
    return {
        "llm_providers": {
            "default": {"provider": "mock", "api_key": "test_value"}
        },
        "mcpServers": {
            "example": {"env": {"EXAMPLE_KEY": "value"}}
        },
    }

def test_resolve_placeholders_simple(mock_env):
    """Test resolving placeholders in strings."""
    assert resolve_placeholders("${TEST_VAR}") == "test_value"

def test_resolve_placeholders_missing():
    """Test missing environment variable raises ValueError."""
    with pytest.raises(ValueError, match="Environment variable 'MISSING_VAR' is not set but is required."):
        resolve_placeholders("${MISSING_VAR}")

def test_load_server_config_valid(mock_env):
    """Test loading a valid server config."""
    mock_data = '{"llm_providers": {"default": {"provider": "mock", "api_key": "${TEST_VAR}"}}}'
    with patch("builtins.open", mock_open(read_data=mock_data)), patch("os.path.exists", return_value=True):
        config = load_server_config("test.json")
        assert config["llm_providers"]["default"]["api_key"] == "test_value"

# TODO test validate api keys when some providers like ollama dont need them?
# def test_validate_api_keys(valid_config, mock_env):
#     """Test validate_api_keys with valid configuration."""
#     assert validate_api_keys(valid_config) == valid_config

def test_are_required_mcp_servers_running(valid_config):
    """Test required MCP servers validation."""
    assert are_required_mcp_servers_running(["example"], valid_config) == (True, [])
    assert are_required_mcp_servers_running(["nonexistent"], valid_config) == (False, ["nonexistent"])
