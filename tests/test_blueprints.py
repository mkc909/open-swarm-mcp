# tests/test_blueprints.py

import os
import sys
import pytest

# Add the project root to sys.path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from open_swarm_mcp.main import discover_blueprints

@pytest.fixture
def blueprints_path():
    return os.path.join(project_root, "blueprints")

def test_discover_blueprints(blueprints_path):
    """
    Test that discover_blueprints finds at least one blueprint.
    """
    blueprints = discover_blueprints(blueprints_path)
    assert isinstance(blueprints, dict), "Blueprints should be returned as a dictionary."
    assert len(blueprints) > 0, "At least one blueprint should be discovered."
    for name, metadata in blueprints.items():
        assert isinstance(name, str), "Blueprint names should be strings."
        assert isinstance(metadata, dict), "Blueprint metadata should be a dictionary."
        assert 'title' in metadata, f"Blueprint '{name}' is missing 'title' in metadata."
        assert 'description' in metadata, f"Blueprint '{name}' is missing 'description' in metadata."
