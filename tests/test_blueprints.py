# tests/test_blueprints.py

import pytest
import importlib.util
from unittest.mock import patch, Mock
from open_swarm_mcp.config.blueprint_discovery import discover_blueprints
from open_swarm_mcp.config.blueprint_selection import prompt_user_to_select_blueprint

@pytest.fixture
def setup_blueprints(tmp_path):
    """
    Fixture to set up a temporary blueprints directory with various blueprints for testing.
    """
    blueprints_dir = tmp_path / "blueprints"
    blueprints_dir.mkdir()

    # 1. Valid Blueprint
    valid_bp_name = "valid_blueprint"
    valid_bp_dir = blueprints_dir / valid_bp_name
    valid_bp_dir.mkdir()
    valid_bp_file = valid_bp_dir / f"blueprint_{valid_bp_name}.py"
    valid_bp_file.write_text("""
from open_swarm_mcp.blueprint_base import BlueprintBase

class ValidBlueprint(BlueprintBase):
    \"\"\"
    A valid blueprint for testing.
    \"\"\"

    def __init__(self, config=None, **kwargs):
        super().__init__(config=config, **kwargs)
        self._metadata = {
            "title": "Valid Blueprint",
            "description": "A valid blueprint for testing.",
            "required_mcp_servers": ["server1"],
            "env_vars": ["ENV_VAR1", "ENV_VAR2"]
        }

    @property
    def metadata(self):
        return self._metadata

    def validate_env_vars(self):
        pass

    def get_agents(self):
        return {}
""")

    # 2. Special Character Blueprint
    special_char_bp_name = "special@blueprint#1"
    special_char_bp_dir = blueprints_dir / special_char_bp_name
    special_char_bp_dir.mkdir()
    special_char_bp_file = special_char_bp_dir / f"blueprint_{special_char_bp_name}.py"
    special_char_bp_file.write_text("""
from open_swarm_mcp.blueprint_base import BlueprintBase

class SpecialCharacterBlueprint(BlueprintBase):
    \"\"\"
    Blueprint with special characters in the name.
    \"\"\"

    def __init__(self, config=None, **kwargs):
        super().__init__(config=config, **kwargs)
        self._metadata = {
            "title": "Special Character Blueprint",
            "description": "Blueprint with special characters in the name.",
            "required_mcp_servers": ["server_special"],
            "env_vars": ["SPECIAL_ENV_VAR"]
        }

    @property
    def metadata(self):
        return self._metadata

    def validate_env_vars(self):
        pass

    def get_agents(self):
        return {}
""")

    return blueprints_dir

def test_prompt_user_to_select_blueprint_single_blueprint(setup_blueprints):
    """
    Test blueprint selection when only one blueprint is available.
    """
    blueprints_metadata = discover_blueprints([str(setup_blueprints)])
    with patch('builtins.input', return_value='1'):
        selected = prompt_user_to_select_blueprint(blueprints_metadata)
    assert selected == "valid_blueprint"

def test_prompt_user_to_select_blueprint_multiple_blueprints(setup_blueprints):
    """
    Test blueprint selection with multiple blueprints and user selecting a valid one.
    """
    blueprints_metadata = discover_blueprints([str(setup_blueprints)])
    # Assuming there are two blueprints: 'valid_blueprint' and 'special@blueprint#1'
    with patch('builtins.input', side_effect=['2']):
        selected = prompt_user_to_select_blueprint(blueprints_metadata)
    assert selected == "special@blueprint#1"

def test_prompt_user_to_select_blueprint_invalid_then_valid(setup_blueprints, caplog):
    """
    Test blueprint selection with invalid input followed by a valid selection.
    """
    blueprints_metadata = discover_blueprints([str(setup_blueprints)])
    with patch('builtins.input', side_effect=['invalid', '2']):
        selected = prompt_user_to_select_blueprint(blueprints_metadata)
    assert selected == "special@blueprint#1"
    assert "Invalid selection" in caplog.text or "Please enter a valid number" in caplog.text

def test_prompt_user_to_select_blueprint_no_blueprints(tmp_path, caplog):
    """
    Test blueprint selection when no blueprints are available.
    """
    empty_dir = tmp_path / "empty_blueprints"
    empty_dir.mkdir()
    blueprints_metadata = discover_blueprints([str(empty_dir)])
    with patch('builtins.input', return_value='1'):
        selected = prompt_user_to_select_blueprint(blueprints_metadata)
    assert selected == "basic.default"
    assert "No blueprints available" in caplog.text
