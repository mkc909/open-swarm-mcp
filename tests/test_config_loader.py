# Updated tests/test_config_loader.py

import pytest
from swarm.config.config_loader import validate_api_keys

def test_validate_api_keys_missing_server_key():
    """
    Test validate_api_keys for missing server key scenarios.
    """
    config = {
        "llm_providers": {
            "grok": {
                "provider": "openai",
                "model": "grok-2-1212",
                "base_url": "https://api.x.ai/v1",
                "api_key": "dummy_xai_key",
                "temperature": 0.0,
            }
        },
        "mcpServers": {
            "brave-search": {
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-brave-search"],
                "env": {"BRAVE_API_KEY": ""},
            },
            "sqlite": {
                "command": "uvx",
                "args": ["mcp-server-sqlite", "--db-path", "test.db"],
                "env": {},
            },
            "filesystem": {
                "command": "bash",
                "args": [
                    "-c",
                    "command -v mcp-filesystem-server >/dev/null 2>&1 || go install github.com/mark3labs/mcp-filesystem-server@latest && ~/go/bin/mcp-filesystem-server $(echo $ALLOWED_PATHS | tr ',' ' ')",
                ],
                "env": {"ALLOWED_PATHS": "/path/to/allowed1,/path/to/allowed2"},
            },
        },
    }

    expected_error_msg = (
        "Environment variable 'BRAVE_API_KEY' for server 'brave-search' is set to an empty value."
    )

    with pytest.raises(ValueError) as exc_info:
        validate_api_keys(config, selected_llm="grok")

    # Updated to match the actual error message
    assert expected_error_msg in str(exc_info.value), "Error message does not match expected"
