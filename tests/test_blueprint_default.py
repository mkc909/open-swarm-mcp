# tests/test_blueprint_default.py

import pytest
import os
import sys
import importlib.util
from unittest.mock import patch, Mock
from pathlib import Path
from shutil import copyfile

# Add the 'src/' directory to sys.path to allow imports from src/
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from open_swarm_mcp.blueprint_base import BlueprintBase

@pytest.fixture
def temporary_blueprints_dir(tmp_path):
    """
    Fixture to create a temporary 'blueprints/' directory containing only the 'default' blueprint.
    
    Args:
        tmp_path (Path): Built-in pytest fixture for temporary directories.
    
    Returns:
        Path: Path to the temporary 'blueprints/' directory.
    """
    # Path to the temporary 'blueprints/' directory
    temp_blueprints = tmp_path / "blueprints"
    temp_blueprints.mkdir()

    # Path to the 'default' blueprint in the original directory
    original_blueprint_dir = Path("blueprints") / "default"
    original_blueprint_file = original_blueprint_dir / "blueprint_default.py"

    # Ensure the original blueprint exists
    assert original_blueprint_file.exists(), f"Blueprint file not found at {original_blueprint_file}"

    # Copy the 'default' blueprint to the temporary directory
    temp_default_dir = temp_blueprints / "default"
    temp_default_dir.mkdir()
    temp_default_file = temp_blueprints / "default" / "blueprint_default.py"
    copyfile(original_blueprint_file, temp_default_file)

    return temp_blueprints

@patch('swarm.Swarm.run')
def test_execute_echo(mock_run, temporary_blueprints_dir):
    """
    Test the execute function to verify that it correctly echoes user inputs.

    Args:
        mock_run (Mock): Mocked Swarm.run method.
        temporary_blueprints_dir (Path): Temporary blueprints directory containing only 'default' blueprint.
    """
    # Discover blueprints using the blueprint_discovery function with the temporary directory
    from open_swarm_mcp.config.blueprint_discovery import discover_blueprints
    blueprints_metadata = discover_blueprints(str(temporary_blueprints_dir))

    assert "default" in blueprints_metadata, "Default blueprint should be discovered."

    default_metadata = blueprints_metadata["default"]

    # Import the execute function dynamically from the temporary blueprint
    blueprint_module_path = temporary_blueprints_dir / "default" / "blueprint_default.py"
    spec = importlib.util.spec_from_file_location("blueprint_default", str(blueprint_module_path))
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except Exception as e:
        pytest.fail(f"Failed to import blueprint_default.py: {e}")

    # Find the blueprint class in the module
    blueprint_class = None
    for attr_name in dir(module):
        attr = getattr(module, attr_name)
        if isinstance(attr, type) and issubclass(attr, BlueprintBase) and attr is not BlueprintBase:
            blueprint_class = attr
            break

    assert blueprint_class is not None, "Blueprint class inheriting from BlueprintBase not found."

    # Instantiate the blueprint
    blueprint_instance = blueprint_class()

    execute = blueprint_instance.execute

    # Define the mock response that Swarm.run should return
    mock_response = Mock()
    # Simulate the assistant's response echoing the user's input
    mock_response.messages = [
        {"role": "assistant", "content": "Hello, how are you?"}
    ]
    mock_run.return_value = mock_response

    # Execute the blueprint
    result = execute()

    # Assertions to verify the response structure and content
    assert result["status"] == "success", "Status should be 'success'."
    assert "messages" in result, "Response should contain 'messages'."
    assert len(result["messages"]) == 1, "There should be exactly one message."
    expected_content = "Hello, how are you?"
    assert result["messages"][0]["content"] == expected_content, "The content of the message is incorrect."
    assert result["metadata"]["title"] == "Default Simple Agent", "Metadata title mismatch."

    # Additionally, verify that Swarm.run was called with the correct parameters
    mock_run.assert_called_once()
    # Extract the arguments with which Swarm.run was called
    run_call_args = mock_run.call_args
    assert 'agent' in run_call_args.kwargs, "Swarm.run should be called with an 'agent'."
    assert 'messages' in run_call_args.kwargs, "Swarm.run should be called with 'messages'."
    # Optionally, verify the agent's instructions or other properties if needed
