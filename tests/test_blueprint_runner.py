# tests/test_blueprint_runner.py

import pytest
from unittest.mock import patch, MagicMock
from swarm.extensions.cli.blueprint_runner import (
    load_blueprint,
    run_blueprint_framework,
    run_blueprint_interactive,
)

@patch("importlib.util.spec_from_file_location")
@patch("importlib.util.module_from_spec")
def test_load_blueprint(mock_module_from_spec, mock_spec):
    """Test loading a blueprint module."""
    mock_spec.return_value = MagicMock()
    mock_module_from_spec.return_value = MagicMock()
    
    module = load_blueprint("/path/to/blueprint_valid.py")
    assert module is not None, "Failed to load blueprint module."
    mock_spec.assert_called_once_with("blueprint_module", "/path/to/blueprint_valid.py")
    mock_module_from_spec.assert_called_once_with(mock_spec.return_value)


def test_run_blueprint_framework():
    """Test running a blueprint in framework mode."""
    mock_blueprint = MagicMock()
    mock_blueprint.execute.return_value = {
        "status": "success",
        "messages": [{"role": "system", "content": "Test message"}],
        "metadata": {"key": "value"},
    }

    with patch("builtins.print") as mock_print:
        run_blueprint_framework(mock_blueprint)
        mock_print.assert_any_call("Execution Result:")
        mock_print.assert_any_call("Status:", "success")
        mock_print.assert_any_call("Metadata:", {"key": "value"})
        mock_blueprint.execute.assert_called_once()


def test_run_blueprint_interactive():
    """Test running a blueprint in interactive mode."""
    mock_blueprint = MagicMock()
    with patch("builtins.print") as mock_print:
        run_blueprint_interactive(mock_blueprint)
        mock_blueprint.interactive_mode.assert_called_once()
        mock_print.assert_not_called()  # No output expected unless there's an error


@patch("swarm.extensions.cli.blueprint_runner.load_blueprint")
@patch("swarm.extensions.cli.blueprint_runner.run_blueprint_framework")
@patch("os.path.isfile", return_value=True)
@patch("sys.argv", ["blueprint_runner.py", "/path/to/blueprint_valid.py"])
def test_main_framework_mode(mock_isfile, mock_run_framework, mock_load_blueprint):
    """Test the CLI for framework mode."""
    from swarm.extensions.cli.blueprint_runner import main
    main()
    mock_load_blueprint.assert_called_once_with("/path/to/blueprint_valid.py")
    mock_run_framework.assert_called_once()


@patch("swarm.extensions.cli.blueprint_runner.load_blueprint")
@patch("swarm.extensions.cli.blueprint_runner.run_blueprint_interactive")
@patch("os.path.isfile", return_value=True)
@patch("sys.argv", ["blueprint_runner.py", "/path/to/blueprint_valid.py", "--interactive"])
def test_main_interactive_mode(mock_isfile, mock_run_interactive, mock_load_blueprint):
    """Test the CLI for interactive mode."""
    from swarm.extensions.cli.blueprint_runner import main
    main()
    mock_load_blueprint.assert_called_once_with("/path/to/blueprint_valid.py")
    mock_run_interactive.assert_called_once()
