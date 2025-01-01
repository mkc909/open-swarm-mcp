"""
Tests for the blueprint discovery module.
"""

import pytest
from open_swarm_mcp.config.blueprint_discovery import discover_blueprints
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


@pytest.fixture
def temporary_blueprints_dir(tmp_path: Path) -> Path:
    """
    Fixture to create a temporary directory with a valid blueprint.
    """
    blueprints_dir = tmp_path / "blueprints"
    blueprints_dir.mkdir()
    valid_blueprint_dir = blueprints_dir / "valid_blueprint"
    valid_blueprint_dir.mkdir()

    blueprint_code = """
from open_swarm_mcp.blueprint_base import BlueprintBase

class ValidBlueprint(BlueprintBase):
    metadata = {
        "title": "Valid Blueprint",
        "description": "This is a valid blueprint for testing."
    }
"""
    (valid_blueprint_dir / "blueprint_valid_blueprint.py").write_text(blueprint_code)

    return blueprints_dir


def test_discover_blueprints_valid(temporary_blueprints_dir, caplog):
    """
    Test that valid blueprints are discovered correctly.
    """
    with caplog.at_level(logging.INFO):
        blueprints = discover_blueprints([str(temporary_blueprints_dir)])

    assert "valid_blueprint" in blueprints, "Valid blueprint should be discovered."
    assert blueprints["valid_blueprint"]["metadata"]["title"] == "Valid Blueprint"
