import pytest
from unittest.mock import patch
from pathlib import Path
from swarm.extensions.blueprint.blueprint_discovery import discover_blueprints

# def test_discover_blueprints_invalid_metadata(tmp_path):
#     """Test a blueprint with invalid metadata."""
#     blueprint_dir = tmp_path / "blueprints"
#     blueprint_dir.mkdir()
#     invalid_metadata_file = blueprint_dir / "blueprint_invalid_metadata.py"
#     invalid_metadata_file.write_text("""
#     from swarm.extensions.blueprint.blueprint_base import BlueprintBase
#     class InvalidMetadataBlueprint(BlueprintBase):
#         @property
#         def metadata(self):
#             return "invalid_metadata"  # Not a dictionary
#         def create_agents(self):
#             return {"agent": "mock_agent"}
#     """)
#     with patch("logging.Logger.error") as mock_error_log:
#         blueprints = discover_blueprints([str(blueprint_dir)])
#         assert blueprints == {}, "Invalid metadata should result in no blueprints discovered."
#         mock_error_log.assert_any_call(
#             "Error retrieving metadata for blueprint 'invalid_metadata': Metadata for blueprint 'invalid_metadata' is invalid or inaccessible."
#         )

# def test_discover_blueprints_missing_metadata(tmp_path):
#     """Test a blueprint with missing metadata."""
#     blueprint_dir = tmp_path / "blueprints"
#     blueprint_dir.mkdir()
#     missing_metadata_file = blueprint_dir / "blueprint_missing_metadata.py"
#     missing_metadata_file.write_text("""
#     from swarm.extensions.blueprint.blueprint_base import BlueprintBase
#     class MissingMetadataBlueprint(BlueprintBase):
#         def create_agents(self):
#             return {"agent": "mock_agent"}
#     """)
#     with patch("logging.Logger.error") as mock_error_log:
#         blueprints = discover_blueprints([str(blueprint_dir)])
#         assert blueprints == {}, "Missing metadata should result in no blueprints discovered."
#         mock_error_log.assert_any_call(
#             "Error retrieving metadata for blueprint 'missing_metadata': Metadata for blueprint 'missing_metadata' is invalid or inaccessible."
#         )

# def test_discover_blueprints_default_metadata(tmp_path):
#     """Test a blueprint with incomplete metadata."""
#     blueprint_dir = tmp_path / "blueprints"
#     blueprint_dir.mkdir()
#     incomplete_metadata_file = blueprint_dir / "blueprint_incomplete_metadata.py"
#     incomplete_metadata_file.write_text("""
#     from swarm.extensions.blueprint.blueprint_base import BlueprintBase
#     class IncompleteMetadataBlueprint(BlueprintBase):
#         @property
#         def metadata(self):
#             return {"title": "Incomplete Blueprint", "description": "Default description"}  # Add required fields
#         def create_agents(self):
#             return {"agent": "mock_agent"}
#     """)
#     blueprints = discover_blueprints([str(blueprint_dir)])
#     assert "incomplete" in blueprints, "Blueprint with complete metadata should be discovered."

# def test_discover_blueprints_default_metadata(tmp_path):
#     """Test a blueprint with incomplete metadata."""
#     blueprint_dir = tmp_path / "blueprints"
#     blueprint_dir.mkdir()
#     incomplete_metadata_file = blueprint_dir / "blueprint_incomplete_metadata.py"
#     incomplete_metadata_file.write_text("""
# from swarm.extensions.blueprint.blueprint_base import BlueprintBase

# class IncompleteMetadataBlueprint(BlueprintBase):
#     @property
#     def metadata(self):
#         return {"title": "Incomplete Blueprint"}  # Missing description

#     def create_agents(self):
#         return {"agent": "mock_agent"}
#     """)

#     blueprints = discover_blueprints([str(blueprint_dir)])
#     assert "incomplete" in blueprints, "Blueprint with incomplete metadata should be discovered."
#     assert blueprints["incomplete"]["title"] == "Incomplete Blueprint"
#     assert blueprints["incomplete"]["description"] == "Blueprint for incomplete", "Default description should be used."


def test_discover_blueprints_multiple_files(tmp_path):
    """Test discovering multiple blueprints in a directory."""
    blueprint_dir = tmp_path / "blueprints"
    blueprint_dir.mkdir()

    # Create multiple blueprint files
    valid_blueprint_file = blueprint_dir / "blueprint_valid.py"
    valid_blueprint_file.write_text("""
from swarm.extensions.blueprint.blueprint_base import BlueprintBase

class ValidBlueprint(BlueprintBase):
    @property
    def metadata(self):
        return {"title": "Valid Blueprint", "description": "A valid test blueprint"}

    def create_agents(self):
        return {"agent": "mock_agent"}
    """)

    another_blueprint_file = blueprint_dir / "blueprint_another.py"
    another_blueprint_file.write_text("""
from swarm.extensions.blueprint.blueprint_base import BlueprintBase

class AnotherBlueprint(BlueprintBase):
    @property
    def metadata(self):
        return {"title": "Another Blueprint", "description": "Another test blueprint"}

    def create_agents(self):
        return {"agent": "mock_agent"}
    """)

    blueprints = discover_blueprints([str(blueprint_dir)])
    assert len(blueprints) == 2, "Both blueprints should be discovered."
    assert "valid" in blueprints
    assert "another" in blueprints


def test_discover_blueprints_non_blueprint_files(tmp_path):
    """Test that non-blueprint files are ignored."""
    blueprint_dir = tmp_path / "blueprints"
    blueprint_dir.mkdir()

    # Create a non-blueprint file
    non_blueprint_file = blueprint_dir / "non_blueprint.py"
    non_blueprint_file.write_text("""
class NonBlueprint:
    pass
    """)

    blueprints = discover_blueprints([str(blueprint_dir)])
    assert blueprints == {}, "Non-blueprint files should be ignored."


def test_discover_blueprints_invalid_directory(tmp_path):
    """Test that invalid directories are skipped."""
    invalid_dir = tmp_path / "invalid_dir"

    with patch("logging.Logger.warning") as mock_warning_log:
        blueprints = discover_blueprints([str(invalid_dir)])
        assert blueprints == {}, "Invalid directories should be skipped."
        mock_warning_log.assert_any_call(f"Invalid directory: {invalid_dir}. Skipping...")