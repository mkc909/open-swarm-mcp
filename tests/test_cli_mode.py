# tests/test_cli_mode.py

import pytest
import asyncio  # Import asyncio
from unittest.mock import patch, Mock
from open_swarm_mcp.modes.cli_mode import run_cli_mode
from swarm import Agent

@pytest.fixture
def mock_agent():
    """
    Provides a mock Agent for testing CLI mode.
    """
    agent = Mock(spec=Agent)
    agent.process = Mock(return_value="Hello, user!")
    return agent

def test_run_cli_mode_exit(mock_agent, capsys):
    """
    Test exiting CLI mode gracefully.
    """
    with patch('builtins.input', side_effect=['exit']):
        asyncio.run(run_cli_mode(mock_agent, colorama_available=True))
        captured = capsys.readouterr()
        assert "Exiting CLI mode." in captured.out

def test_run_cli_mode_handle_query(mock_agent, capsys):
    """
    Test handling a user query in CLI mode.
    """
    # Mock the Swarm().run() method to return a mock response
    with patch('open_swarm_mcp.modes.cli_mode.Swarm') as mock_swarm:
        mock_swarm_instance = mock_swarm.return_value
        mock_response = Mock()
        mock_response.messages = [{"role": "assistant", "content": "Hello, user!"}]
        mock_swarm_instance.run.return_value = mock_response

        with patch('builtins.input', side_effect=['Hello', 'exit']):
            asyncio.run(run_cli_mode(mock_agent, colorama_available=True))
            captured = capsys.readouterr()
            assert "Response: Hello, user!" in captured.out
            assert "Exiting CLI mode." in captured.out
