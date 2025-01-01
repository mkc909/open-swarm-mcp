# tests/test_blueprint_discovery.py

import pytest
import tempfile
import shutil
import os
import importlib.util
from pathlib import Path
from unittest.mock import patch, Mock

from open_swarm_mcp.config.blueprint_discovery import discover_blueprints

# Configure logger for the test module (optional but useful for debugging)
import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
if not logger.hasHandlers():
    logger.addHandler(handler)

@pytest.fixture
def temporary_blueprints_dir(tmp_path):
    """
    Fixture to create a temporary 'blueprints/' directory with various blueprints for testing.
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
from swarm import Agent

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

    # 2. Blueprint Missing Metadata
    missing_meta_bp_name = "missing_metadata"
    missing_meta_bp_dir = blueprints_dir / missing_meta_bp_name
    missing_meta_bp_dir.mkdir()
    missing_meta_bp_file = missing_meta_bp_dir / f"blueprint_{missing_meta_bp_name}.py"
    missing_meta_bp_file.write_text("""
# This blueprint lacks EXAMPLE_METADATA
from open_swarm_mcp.blueprint_base import BlueprintBase

class MissingMetadataBlueprint(BlueprintBase):
    def __init__(self, config=None, **kwargs):
        super().__init__(config=config, **kwargs)

    @property
    def metadata(self):
        return {}
    
    def validate_env_vars(self):
        pass

    def get_agents(self):
        return {}
""")

    # 3. Blueprint with Invalid Metadata
    invalid_meta_bp_name = "invalid_metadata"
    invalid_meta_bp_dir = blueprints_dir / invalid_meta_bp_name
    invalid_meta_bp_dir.mkdir()
    invalid_meta_bp_file = invalid_meta_bp_dir / f"blueprint_{invalid_meta_bp_name}.py"
    invalid_meta_bp_file.write_text("""
from open_swarm_mcp.blueprint_base import BlueprintBase

class InvalidMetadataBlueprint(BlueprintBase):
    def __init__(self, config=None, **kwargs):
        super().__init__(config=config, **kwargs)
        # Metadata is a string instead of a dictionary
        self._metadata = "This should be a dictionary."

    @property
    def metadata(self):
        return self._metadata

    def validate_env_vars(self):
        pass

    def get_agents(self):
        return {}
""")

    # 4. Non-conforming Blueprint File
    non_conforming_bp_dir = blueprints_dir / "non_conforming_blueprint"
    non_conforming_bp_dir.mkdir()
    non_conforming_bp_file = non_conforming_bp_dir / "some_other_file.py"
    non_conforming_bp_file.write_text("""
# This file does not define a Blueprint class
def some_function():
    pass
""")

    # 5. Blueprint with Special Characters in Name
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

def test_discover_blueprints_valid(temporary_blueprints_dir, caplog):
    """
    Test that discover_blueprints correctly identifies and loads a valid blueprint.
    """
    with caplog.at_level(logging.INFO):
        blueprints = discover_blueprints([str(temporary_blueprints_dir)])
    
    assert "valid_blueprint" in blueprints, "Valid blueprint should be discovered."
    assert blueprints["valid_blueprint"]["title"] == "Valid Blueprint", "Blueprint title mismatch."
    assert blueprints["valid_blueprint"]["description"] == "A valid blueprint for testing.", "Blueprint description mismatch."
    assert blueprints["valid_blueprint"]["required_mcp_servers"] == ["server1"], "Blueprint required_mcp_servers mismatch."
    assert blueprints["valid_blueprint"]["env_vars"] == ["ENV_VAR1", "ENV_VAR2"], "Blueprint env_vars mismatch."
    assert "Discovered blueprint 'valid_blueprint'" in caplog.text, "Discovery log for valid blueprint missing."

def test_discover_blueprints_missing_metadata(temporary_blueprints_dir, caplog):
    """
    Test that discover_blueprints skips blueprints missing required metadata.
    """
    with caplog.at_level(logging.WARNING):
        blueprints = discover_blueprints([str(temporary_blueprints_dir)])
    
    assert "missing_metadata" not in blueprints, "Blueprint with missing metadata should be skipped."
    assert "EXAMPLE_METADATA in" in caplog.text or "is not a dictionary" in caplog.text, "Warning for missing metadata not logged."

def test_discover_blueprints_invalid_metadata(temporary_blueprints_dir, caplog):
    """
    Test that discover_blueprints skips blueprints with invalid metadata types.
    """
    with caplog.at_level(logging.WARNING):
        blueprints = discover_blueprints([str(temporary_blueprints_dir)])
    
    assert "invalid_metadata" not in blueprints, "Blueprint with invalid metadata should be skipped."
    assert "is not a dictionary" in caplog.text, "Warning for invalid metadata type not logged."

def test_discover_blueprints_non_conforming(temporary_blueprints_dir, caplog):
    """
    Test that discover_blueprints skips non-conforming blueprint files.
    """
    with caplog.at_level(logging.WARNING):
        blueprints = discover_blueprints([str(temporary_blueprints_dir)])
    
    assert "non_conforming_blueprint" not in blueprints, "Non-conforming blueprint should be skipped."
    assert "is not a blueprint class" in caplog.text or "does not define a Blueprint class" in caplog.text, "Warning for non-conforming blueprint not logged."

def test_discover_blueprints_special_characters(temporary_blueprints_dir, caplog):
    """
    Test that discover_blueprints correctly handles blueprints with special characters in their names.
    """
    with caplog.at_level(logging.INFO):
        blueprints = discover_blueprints([str(temporary_blueprints_dir)])
    
    assert "special@blueprint#1" in blueprints, "Blueprint with special characters should be discovered."
    assert blueprints["special@blueprint#1"]["title"] == "Special Character Blueprint", "Special character blueprint title mismatch."
    assert "Discovered blueprint 'special@blueprint#1'" in caplog.text, "Discovery log for special character blueprint missing."

def test_discover_blueprints_no_blueprints(tmp_path, caplog):
    """
    Test that discover_blueprints handles directories with no blueprints gracefully.
    """
    empty_dir = tmp_path / "empty_blueprints"
    empty_dir.mkdir()

    with caplog.at_level(logging.WARNING):
        blueprints = discover_blueprints([str(empty_dir)])
    
    assert len(blueprints) == 0, "No blueprints should be discovered in an empty directory."
    assert "Blueprint directory" in caplog.text or "does not exist or is not a directory" in caplog.text, "Warning for empty blueprint directory not logged."

def test_discover_multiple_directories(temporary_blueprints_dir, caplog, tmp_path):
    """
    Test that discover_blueprints can discover blueprints from multiple directories.
    """
    # Create another valid blueprint in a different directory
    another_dir = tmp_path / "another_blueprints"
    another_dir.mkdir()
    another_bp_name = "another_valid_blueprint"
    another_bp_dir = another_dir / another_bp_name
    another_bp_dir.mkdir()
    another_bp_file = another_bp_dir / f"blueprint_{another_bp_name}.py"
    another_bp_file.write_text("""
from open_swarm_mcp.blueprint_base import BlueprintBase

class AnotherValidBlueprint(BlueprintBase):
    \"\"\"
    Another valid blueprint for testing multiple directories.
    \"\"\"

    def __init__(self, config=None, **kwargs):
        super().__init__(config=config, **kwargs)
        self._metadata = {
            "title": "Another Valid Blueprint",
            "description": "Another valid blueprint for testing multiple directories.",
            "required_mcp_servers": ["server2"],
            "env_vars": ["ENV_VAR3"]
        }

    @property
    def metadata(self):
        return self._metadata

    def validate_env_vars(self):
        pass

    def get_agents(self):
        return {}
""")

    with caplog.at_level(logging.INFO):
        blueprints = discover_blueprints([str(temporary_blueprints_dir), str(another_dir)])
    
    assert "valid_blueprint" in blueprints, "Valid blueprint from first directory should be discovered."
    assert "another_valid_blueprint" in blueprints, "Valid blueprint from second directory should be discovered."
    assert blueprints["another_valid_blueprint"]["title"] == "Another Valid Blueprint", "Another blueprint title mismatch."
    assert "Discovered blueprint 'another_valid_blueprint'" in caplog.text, "Discovery log for another blueprint missing."
