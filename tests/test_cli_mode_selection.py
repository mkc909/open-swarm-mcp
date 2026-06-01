import pytest
from unittest.mock import patch
from swarm.extensions.cli.selection import prompt_user_to_select_blueprint

@patch("builtins.input", return_value="1")
def test_valid_input(mock_input):
    blueprints_metadata = {
        "blueprint1": {
            "title": "Blueprint One",
            "description": "The first blueprint.",
        },
        "blueprint2": {
            "title": "Blueprint Two",
            "description": "The second blueprint.",
        },
    }

    with patch("builtins.print") as mock_print:
        result = prompt_user_to_select_blueprint(blueprints_metadata)

        # Verify the selected blueprint
        assert result == "blueprint1", "The selected blueprint should match the user input."

        # Verify that the print statement for "Available Blueprints:" is present
        assert any(
            call_args[0][0].strip() == "Available Blueprints:"
            for call_args in mock_print.call_args_list
        ), "Expected 'Available Blueprints:' to be printed."
