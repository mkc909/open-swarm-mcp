# Updated tests/test_blueprint_discovery.py

import pytest
import logging
from open_swarm_mcp.config.blueprint_discovery import discover_blueprints

@pytest.fixture
def temporary_blueprints_dir(tmp_path):
    """
    Fixture to create a temporary 'blueprints/' directory with various blueprints for testing.
    """
    blueprints_dir = tmp_path / "blueprints"
    blueprints_dir.mkdir()

    # Create a temporary configuration file for BlueprintBase
    config_file = tmp_path / "mcp_server_config.json"
    config_file.write_text("""
    {
        "llm_providers": {
            "default": {
                "provider": "openai",
                "model": "gpt-4o",
                "base_url": "https://api.openai.com/v1",
                "api_key": "dummy_api_key",
                "temperature": 0.7
            }
        },
        "mcpServers": {}
    }
    """)

    # Valid Blueprint
    valid_bp_dir = blueprints_dir / "valid_blueprint"
    valid_bp_dir.mkdir()
    (valid_bp_dir / "blueprint_valid_blueprint.py").write_text(f"""
from open_swarm_mcp.blueprint_base import BlueprintBase

class ValidBlueprint(BlueprintBase):
    def __init__(self):
        # Pass the temporary configuration file path
        super().__init__(config_path="{config_file}")
        self._metadata = {{
            "title": "Valid Blueprint",
            "description": "A valid blueprint for testing.",
            "required_mcp_servers": ["server1"],
            "env_vars": ["ENV_VAR1", "ENV_VAR2"]
        }}

    @property
    def metadata(self):
        return self._metadata

    def execute(self):
        pass

    def validate_env_vars(self):
        pass

    def get_agents(self):
        return {{}}
    """)

    return blueprints_dir


def test_discover_blueprints_valid(temporary_blueprints_dir, caplog):
    with caplog.at_level(logging.INFO):
        blueprints = discover_blueprints([str(temporary_blueprints_dir)])
    assert "valid_blueprint" in blueprints, "Valid blueprint should be discovered."
    assert blueprints["valid_blueprint"]["title"] == "Valid Blueprint"
