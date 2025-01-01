"""
Tests for the blueprint discovery module.
"""

import pytest
from swarm.config.blueprint_discovery import discover_blueprints
from pathlib import Path
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


@pytest.fixture
def temporary_blueprints_dir(tmp_path: Path) -> Path:
    """
    Fixture to create a temporary directory with a valid blueprint.
    """
    logger.info("Setting up temporary blueprint directory.")

    blueprints_dir = tmp_path / "blueprints"
    blueprints_dir.mkdir()

    valid_blueprint_dir = blueprints_dir / "valid_blueprint"
    valid_blueprint_dir.mkdir()

    blueprint_code = '''
from swarm.blueprint_base import BlueprintBase

class ValidBlueprint(BlueprintBase):
    @property
    def metadata(self):
        return {
            "title": "Valid Blueprint",
            "description": "This is a valid blueprint for testing."
        }
'''
    blueprint_file = valid_blueprint_dir / "blueprint_valid_blueprint.py"
    blueprint_file.write_text(blueprint_code)

    logger.debug(f"Created test blueprint file at: {blueprint_file}")
    return blueprints_dir


def test_discover_blueprints_valid(temporary_blueprints_dir, caplog):
    """
    Test that valid blueprints are discovered correctly.
    """
    caplog.set_level(logging.DEBUG)
    logger.info(f"Temporary blueprint directory: {temporary_blueprints_dir}")

    # Run discovery
    blueprints = discover_blueprints([str(temporary_blueprints_dir)])

    # Assert the blueprint is discovered
    assert "valid_blueprint" in blueprints, "Valid blueprint should be discovered."

    # Validate the metadata
    metadata = blueprints["valid_blueprint"]  # Adjusted to access metadata directly
    assert metadata["title"] == "Valid Blueprint", "Blueprint title is incorrect."
    assert metadata["description"] == "This is a valid blueprint for testing.", "Blueprint description is incorrect."

    logger.info("Blueprint discovery test completed successfully.")
