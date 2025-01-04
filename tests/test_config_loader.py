import pytest
from unittest.mock import patch, mock_open
from swarm.extensions.config.config_loader import (
    resolve_placeholders,
    load_server_config,
    validate_api_keys,
    are_required_mcp_servers_configured,
    load_llm_config,
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

def test_are_required_mcp_servers_configured(valid_config):
    """Test required MCP servers validation."""
    assert are_required_mcp_servers_configured(["example"], valid_config) == (True, [])
    assert are_required_mcp_servers_configured(["nonexistent"], valid_config) == (False, ["nonexistent"])

@patch("builtins.open", mock_open(read_data='{"api_key": "${TEST_API_KEY}"}'))
@patch("os.getenv", return_value="mock_api_key")
def test_load_server_config_with_placeholders(mock_getenv):
    """Test loading configuration with placeholders."""
    config = load_server_config()
    assert config["api_key"] == "mock_api_key"
    mock_getenv.assert_called_once_with("TEST_API_KEY")

@patch("builtins.open", mock_open(read_data='{"api_key": "${MISSING_API_KEY}"}'))
def test_load_server_config_with_missing_placeholder():
    """Test loading configuration with a missing environment variable."""
    with pytest.raises(ValueError, match="Environment variable 'MISSING_API_KEY' is not set but is required."):
        load_server_config()

@patch("os.getcwd", return_value="/mock/path")
@patch("builtins.open", mock_open(read_data='{"key": "value"}'))
def test_load_server_config_default_path(mock_getcwd):
    """Test loading configuration from the default path."""
    config = load_server_config()
    assert config["key"] == "value"
    mock_getcwd.assert_called_once()

def test_load_llm_config_specific_llm(valid_config):
    """Test loading a specified LLM configuration."""
    config = {
        "llm": {
            "openai": {"provider": "openai", "api_key": "mock_key"},
            "default": {"provider": "mock", "api_key": "test_value"}
        }
    }
    llm_config = load_llm_config(config, llm_name="openai")
    assert llm_config == {"provider": "openai", "api_key": "mock_key"}

@patch.dict("os.environ", {"DEFAULT_LLM": "openai"})
def test_load_llm_config_envvar_fallback(valid_config):
    """Test loading LLM configuration using DEFAULT_LLM environment variable."""
    config = {
        "llm": {
            "openai": {"provider": "openai", "api_key": "mock_key"},
            "default": {"provider": "mock", "api_key": "test_value"}
        }
    }
    llm_config = load_llm_config(config)
    assert llm_config == {"provider": "openai", "api_key": "mock_key"}
