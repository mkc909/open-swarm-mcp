"""
Tests for Blueprint Discovery and Selection.

This module tests the discovery of blueprints in a directory structure
and user selection of blueprints via the command-line interface.

The test cases validate:
1. Discovery of blueprints with correctly implemented metadata.
2. Skipping of blueprints missing the metadata property.
3. User selection functionality when multiple blueprints are available.

Dependencies:
- pytest for test execution.
- unittest.mock for patching user inputs.
"""

import pytest
from unittest.mock import patch
from swarm.extensions.blueprint import discover_blueprints
from swarm.extensions.cli.selection import prompt_user_to_select_blueprint


@pytest.fixture
def setup_blueprints(tmp_path):
    """
    Fixture to set up a temporary blueprints directory with various blueprints for testing.

    Creates:
    - A valid blueprint with correctly implemented metadata.
    - A blueprint missing the metadata property.
    """
    blueprints_dir = tmp_path / "blueprints"
    blueprints_dir.mkdir()

    # 1. Valid Blueprint
    valid_bp_name = "valid_blueprint"
    valid_bp_dir = blueprints_dir / valid_bp_name
    valid_bp_dir.mkdir()
    valid_bp_file = valid_bp_dir / f"blueprint_{valid_bp_name}.py"
    valid_bp_file.write_text("""
from swarm.extensions.blueprint import BlueprintBase

class ValidBlueprint(BlueprintBase):
    \"\"\"
    A valid blueprint for testing.
    \"\"\"

    @property
    def metadata(self):
        return {
            "title": "Valid Blueprint",
            "description": "A valid blueprint for testing.",
            "required_mcp_servers": ["server1"],
            "env_vars": ["ENV_VAR1", "ENV_VAR2"]
        }

    def create_agents(self):
        pass
""")

    # 2. Blueprint with Missing Metadata
    missing_metadata_bp_name = "missing_metadata"
    missing_metadata_bp_dir = blueprints_dir / missing_metadata_bp_name
    missing_metadata_bp_dir.mkdir()
    missing_metadata_bp_file = missing_metadata_bp_dir / f"blueprint_{missing_metadata_bp_name}.py"
    missing_metadata_bp_file.write_text("""
from swarm.extensions.blueprint import BlueprintBase

class MissingMetadataBlueprint(BlueprintBase):
    \"\"\"
    A blueprint with no metadata property.
    \"\"\"

    def create_agents(self):
        pass
""")

    return blueprints_dir


def test_discover_valid_blueprint(setup_blueprints):
    """
    Test that a valid blueprint is discovered and its metadata is correctly parsed.

    Validates:
    - The blueprint is listed in the discovery output.
    - Metadata attributes (title, description) are accurately extracted.
    """
    blueprints_metadata = discover_blueprints([str(setup_blueprints)])
    assert "valid_blueprint" in blueprints_metadata
    metadata = blueprints_metadata["valid_blueprint"]
    assert metadata["title"] == "Valid Blueprint"
    assert metadata["description"] == "A valid blueprint for testing."


def test_discover_missing_metadata_blueprint(setup_blueprints):
    """
    Test behavior when discovering a blueprint without a metadata property.

    Validates:
    - Blueprints missing the metadata property are excluded from discovery.
    """
    blueprints_metadata = discover_blueprints([str(setup_blueprints)])
    assert "missing_metadata" not in blueprints_metadata


def test_prompt_user_to_select_blueprint_multiple_blueprints(setup_blueprints):
    """
    Test blueprint selection with multiple blueprints and user selecting a valid one.

    Simulates:
    - User input via mock patching to select the first blueprint.
    - Selection is correctly reflected in the output.
    """
    blueprints_metadata = discover_blueprints([str(setup_blueprints)])
    with patch('builtins.input', side_effect=['1']):
        selected = prompt_user_to_select_blueprint(blueprints_metadata)
    assert selected == "valid_blueprint"
