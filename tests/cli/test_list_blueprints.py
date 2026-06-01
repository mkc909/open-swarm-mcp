"""
Test case for the list_blueprints command.
"""

from unittest.mock import patch
from swarm.extensions.cli.commands.list_blueprints import execute


def test_execute(capsys):
    """Test the execute function."""
    mock_discover_return = {
        "blueprint1": {"title": "Test Blueprint 1"},
        "blueprint2": {"title": "Test Blueprint 2"},
    }

    with patch(
        "swarm.extensions.cli.commands.list_blueprints.discover_blueprints",
        return_value=mock_discover_return,
    ):
        execute()

    captured = capsys.readouterr()
    assert "Blueprint ID: blueprint1, Title: Test Blueprint 1" in captured.out
    assert "Blueprint ID: blueprint2, Title: Test Blueprint 2" in captured.out
