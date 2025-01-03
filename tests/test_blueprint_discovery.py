"""
Tests for the blueprint discovery module.
"""

import pytest
from unittest.mock import patch, MagicMock
from swarm.extensions.blueprint import discover_blueprints
from pathlib import Path

@patch("swarm.extensions.blueprint.blueprint_base.Swarm", return_value=None)
@patch("os.path.isdir", return_value=True)
@patch("swarm.extensions.blueprint.blueprint_discovery.Path.rglob")
@patch("swarm.extensions.blueprint.blueprint_discovery.importlib.util.spec_from_file_location")
@patch("swarm.extensions.blueprint.blueprint_discovery.importlib.util.module_from_spec")
def test_discover_blueprints_valid(mock_module_from_spec, mock_spec, mock_rglob, mock_isdir, mock_swarm):
    """Test discovering valid blueprints."""
    # Mock valid blueprint file discovery
    mock_file = MagicMock()
    mock_file.stem = "blueprint_valid"
    mock_file.parent = Path("/mock/path")
    mock_rglob.return_value = [mock_file]

    # Mock imported module and class
    mock_module = MagicMock()
    mock_class = MagicMock()
    mock_class.metadata = {"title": "Valid Blueprint", "description": "A test blueprint."}
    mock_class.return_value = mock_class  # Mock instantiation
    mock_module.ValidBlueprint = mock_class
    mock_module_from_spec.return_value = mock_module
    mock_spec.return_value = MagicMock(loader=MagicMock(exec_module=MagicMock()))

    # Run blueprint discovery
    blueprints = discover_blueprints(["/mock/path"])

    # Validate discovered blueprints
    assert "valid" in blueprints
    assert blueprints["valid"]["title"] == "Valid Blueprint"
    assert blueprints["valid"]["description"] == "A test blueprint."


@patch("os.path.isdir", return_value=True)
@patch("swarm.extensions.blueprint.blueprint_discovery.Path.rglob")
def test_discover_blueprints_empty(mock_rglob, mock_isdir):
    """Test discovering blueprints in an empty directory."""
    # Mock empty directory
    mock_rglob.return_value = []

    blueprints = discover_blueprints(["/empty/path"])
    assert blueprints == {}, "Blueprints should be empty for an empty directory."


@patch("swarm.extensions.blueprint.blueprint_discovery.importlib.util.spec_from_file_location")
@patch("os.path.isdir", return_value=True)
def test_discover_blueprints_import_error(mock_spec, mock_isdir):
    """Test discovering blueprints when an import error occurs."""
    # Mock import error
    mock_spec.side_effect = ImportError("Mock import error")

    with pytest.raises(ImportError):
        discover_blueprints(["/mock/path"])
