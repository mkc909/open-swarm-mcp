import pytest
from unittest.mock import patch
from swarm.extensions.blueprint.modes.cli_mode.selection import prompt_user_to_select_blueprint


def test_no_blueprints():
    """Test when no blueprints are available."""
    with patch("builtins.print") as mock_print, patch("logging.Logger.warning") as mock_log:
        result = prompt_user_to_select_blueprint({})
        assert result == "basic.default"
        mock_print.assert_any_call("No blueprints available. Using default blueprint.")
        mock_log.assert_called_once_with("No blueprints available. Using default blueprint.")


@patch("builtins.input", side_effect=["1"])
def test_valid_input(mock_input):
    """Test selecting a valid blueprint."""
    blueprints_metadata = {
        "blueprint_1": {"title": "Blueprint 1", "description": "Description 1"},
        "blueprint_2": {"title": "Blueprint 2", "description": "Description 2"},
    }
    with patch("builtins.print") as mock_print, patch("logging.Logger.debug") as mock_log:
        result = prompt_user_to_select_blueprint(blueprints_metadata)
        assert result == "blueprint_1"
        mock_print.assert_any_call("Available Blueprints:")
        mock_log.assert_any_call("User selected blueprint: 'blueprint_1'")


@patch("builtins.input", side_effect=["0"])
def test_default_input(mock_input):
    """Test selecting the default blueprint."""
    blueprints_metadata = {
        "blueprint_1": {"title": "Blueprint 1", "description": "Description 1"},
    }
    with patch("builtins.print") as mock_print, patch("logging.Logger.info") as mock_log:
        result = prompt_user_to_select_blueprint(blueprints_metadata)
        assert result == "basic.default"
        mock_log.assert_any_call("User chose to use default blueprint 'basic.default'")


@patch("builtins.input", side_effect=["abc", "-1", "3", "1"])
def test_invalid_inputs(mock_input):
    """Test handling of invalid inputs."""
    blueprints_metadata = {
        "blueprint_1": {"title": "Blueprint 1", "description": "Description 1"},
        "blueprint_2": {"title": "Blueprint 2", "description": "Description 2"},
    }
    with patch("builtins.print") as mock_print, patch("logging.Logger.warning") as mock_log:
        result = prompt_user_to_select_blueprint(blueprints_metadata)
        assert result == "blueprint_1"
        mock_print.assert_any_call("Invalid input. Please enter a valid number.")
        mock_print.assert_any_call("Please enter a number between 0 and 2.")
        mock_log.assert_any_call("User entered non-integer value for blueprint selection")
        mock_log.assert_any_call("User entered invalid blueprint number: -1")
