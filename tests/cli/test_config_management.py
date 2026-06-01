"""
Test case for the config_management module.
"""

from unittest.mock import patch
from swarm.extensions.cli.commands.config_management import add_llm


def test_add_llm(capsys):
    """Test adding an LLM configuration."""
    mock_config = {"llms": {}}
    with patch("swarm.extensions.cli.commands.config_management.load_server_config", return_value=mock_config) as mock_load, \
         patch("swarm.extensions.cli.commands.config_management.save_server_config") as mock_save:
        add_llm("gpt-3", "mock-api-key")

    mock_load.assert_called_once()
    mock_save.assert_called_once_with({"llms": {"gpt-3": {"api_key": "mock-api-key"}}})
    captured = capsys.readouterr()
    assert "Added LLM 'gpt-3' to configuration." in captured.out
