"""
Tests for the blueprint discovery module.

This module tests the discovery of blueprints in a directory structure,
validates their metadata, and ensures proper logging during the process.
"""

import pytest
from swarm.extensions.blueprint import discover_blueprints
from pathlib import Path
import logging

# Configure logger for the test module
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


@pytest.fixture
def temporary_blueprints_dir(tmp_path: Path) -> Path:
    """
    Fixture to create a temporary directory with a valid blueprint for testing.

    The blueprint includes:
    - A `metadata` property defining title and description.
    - A `create_agents` method to satisfy the abstract base class requirement.
    """
    logger.info("Setting up temporary blueprint directory.")

    # Create the blueprints directory
    blueprints_dir = tmp_path / "blueprints"
    blueprints_dir.mkdir()

    # Create a subdirectory for the valid blueprint
    valid_blueprint_dir = blueprints_dir / "valid_blueprint"
    valid_blueprint_dir.mkdir()

    # Define the content of the blueprint Python file
    blueprint_code = '''
from swarm.extensions.blueprint import BlueprintBase

class ValidBlueprint(BlueprintBase):
    """
    A valid blueprint for testing.
    """

    @property
    def metadata(self):
        return {
            "title": "Valid Blueprint",
            "description": "This is a valid blueprint for testing."
        }

    def create_agents(self):
        pass
'''

    # Write the blueprint code to a file
    blueprint_file = valid_blueprint_dir / "blueprint_valid_blueprint.py"
    blueprint_file.write_text(blueprint_code)

    logger.debug(f"Created test blueprint file at: {blueprint_file}")
    return blueprints_dir


def test_discover_blueprints_valid(temporary_blueprints_dir, caplog):
    """
    Test that valid blueprints are discovered correctly and their metadata is accurate.

    Steps:
    - Discover blueprints from the temporary directory.
    - Assert that the expected blueprint is found.
    - Validate the title and description metadata.
    """
    caplog.set_level(logging.DEBUG)
    logger.info(f"Temporary blueprint directory: {temporary_blueprints_dir}")

    # Run blueprint discovery
    blueprints = discover_blueprints([str(temporary_blueprints_dir)])

    # Assert the valid blueprint is discovered
    assert "valid_blueprint" in blueprints, "Valid blueprint should be discovered."

    # Validate the metadata of the discovered blueprint
    metadata = blueprints["valid_blueprint"]
    assert metadata["title"] == "Valid Blueprint", "Blueprint title is incorrect."
    assert metadata["description"] == "This is a valid blueprint for testing.", "Blueprint description is incorrect."

    logger.info("Blueprint discovery test completed successfully.")
