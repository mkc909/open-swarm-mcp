# tests/test_blueprints.py

import pytest
import os
import logging
from unittest.mock import patch
from open_swarm_mcp.config.blueprint_discovery import discover_blueprints
from open_swarm_mcp.config.blueprint_selection import prompt_user_to_select_blueprint

@pytest.fixture
def setup_blueprints(tmp_path):
    """
    Fixture to set up a temporary blueprints directory with various blueprints for testing.
    """
    blueprints_dir = tmp_path / "blueprints"
    blueprints_dir.mkdir()

    # Valid blueprint
    valid_blueprint_name = "valid_blueprint"
    valid_blueprint_dir = blueprints_dir / valid_blueprint_name
    valid_blueprint_dir.mkdir()
    valid_blueprint_file = valid_blueprint_dir / f"blueprint_{valid_blueprint_name}.py"
    valid_blueprint_file.write_text("""
EXAMPLE_METADATA = {
    "title": "Valid Blueprint",
    "description": "A valid blueprint for testing.",
    "required_mcp_servers": ["server1", "server2"],
    "env_vars": ["ENV_VAR1", "ENV_VAR2"],
    "default_args": "--default-args"
}
""")

    # Blueprint missing EXAMPLE_METADATA
    missing_metadata_name = "missing_metadata"
    missing_metadata_dir = blueprints_dir / missing_metadata_name
    missing_metadata_dir.mkdir()
    missing_metadata_file = missing_metadata_dir / f"blueprint_{missing_metadata_name}.py"
    missing_metadata_file.write_text("""
# No EXAMPLE_METADATA defined here
""")

    # Blueprint with invalid EXAMPLE_METADATA
    invalid_metadata_name = "invalid_metadata"
    invalid_metadata_dir = blueprints_dir / invalid_metadata_name
    invalid_metadata_dir.mkdir()
    invalid_metadata_file = invalid_metadata_dir / f"blueprint_{invalid_metadata_name}.py"
    invalid_metadata_file.write_text("""
EXAMPLE_METADATA = "This should be a dictionary, not a string."
""")

    # Non-conforming blueprint file
    non_conforming_name = "non_conforming_blueprint"
    non_conforming_dir = blueprints_dir / non_conforming_name
    non_conforming_dir.mkdir()
    non_conforming_file = non_conforming_dir / "some_other_file.py"
    non_conforming_file.write_text("""
# This file does not follow the blueprint naming convention
""")

    # Blueprint with special characters
    special_char_name = "special@blueprint#1"
    special_char_dir = blueprints_dir / special_char_name
    special_char_dir.mkdir()
    special_char_file = special_char_dir / f"blueprint_{special_char_name}.py"
    special_char_file.write_text("""
EXAMPLE_METADATA = {
    "title": "Special Character Blueprint",
    "description": "Blueprint with special characters in the name.",
    "required_mcp_servers": ["server_special"],
    "env_vars": ["SPECIAL_ENV"],
    "default_args": "--special-args"
}
""")

    return blueprints_dir

def test_discover_blueprints(setup_blueprints, caplog):
    """
    Test blueprint discovery with various blueprints.
    """
    with caplog.at_level(logging.WARNING):
        blueprints = discover_blueprints(str(setup_blueprints))
        assert "valid_blueprint" in blueprints
        assert blueprints["valid_blueprint"]['title'] == "Valid Blueprint"
        assert "missing_metadata" not in blueprints
        assert "invalid_metadata" not in blueprints
        assert "non_conforming_blueprint" not in blueprints
        assert "special@blueprint#1" in blueprints
        assert blueprints["special@blueprint#1"]['title'] == "Special Character Blueprint"

        # Check that warnings were logged for missing and invalid metadata
        assert "EXAMPLE_METADATA in" in caplog.text
        assert "is not a dictionary. Skipping blueprint." in caplog.text

def test_discover_no_blueprints(tmp_path, caplog):
    """
    Test blueprint discovery when no blueprints are present.
    """
    blueprints_dir = tmp_path / "blueprints"
    blueprints_dir.mkdir()
    blueprints_metadata = discover_blueprints(str(blueprints_dir))
    assert len(blueprints_metadata) == 0

def test_discover_blueprint_with_invalid_metadata(setup_blueprints, caplog):
    """
    Test that blueprints with invalid EXAMPLE_METADATA are skipped and warnings are logged.
    """
    with caplog.at_level(logging.WARNING):
        blueprints = discover_blueprints(str(setup_blueprints))
        assert "invalid_metadata" not in blueprints
        assert "EXAMPLE_METADATA in" in caplog.text
        assert "is not a dictionary. Skipping blueprint." in caplog.text

def test_prompt_user_to_select_blueprint(setup_blueprints):
    """
    Test blueprint selection prompt with various user inputs.
    """
    blueprints_metadata = discover_blueprints(str(setup_blueprints))

    # Mock user selecting the first blueprint
    with patch('builtins.input', return_value='1'):
        selected = prompt_user_to_select_blueprint(blueprints_metadata)
        assert selected == "valid_blueprint"

    # Mock user selecting default
    with patch('builtins.input', return_value='0'):
        selected = prompt_user_to_select_blueprint(blueprints_metadata)
        assert selected == "basic.default"

    # Mock user entering invalid input followed by a valid selection
    with patch('builtins.input', side_effect=['invalid', '2']):
        selected = prompt_user_to_select_blueprint(blueprints_metadata)
        assert selected == "special@blueprint#1"

    # Mock user entering out-of-range number followed by a valid selection
    with patch('builtins.input', side_effect=['10', '1']):
        selected = prompt_user_to_select_blueprint(blueprints_metadata)
        assert selected == "valid_blueprint"

    # Mock user entering non-integer values followed by default
    with patch('builtins.input', side_effect=['abc', '0']):
        selected = prompt_user_to_select_blueprint(blueprints_metadata)
        assert selected == "basic.default"

def test_prompt_user_to_select_blueprint_no_blueprints(tmp_path, caplog):
    """
    Test blueprint selection when no blueprints are available.
    """
    blueprints_dir = tmp_path / "blueprints"
    blueprints_dir.mkdir()
    blueprints_metadata = discover_blueprints(str(blueprints_dir))
    with caplog.at_level(logging.WARNING):
        selected = prompt_user_to_select_blueprint(blueprints_metadata)
        assert selected == "basic.default"
        assert "No blueprints available. Using default blueprint." in caplog.text
