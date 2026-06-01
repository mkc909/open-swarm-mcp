import os
import sys
import pytest

def test_swarm_cli_install_creates_executable(monkeypatch, tmp_path, capsys):
    import os
    # Create a dummy blueprint file
    blueprint_path = tmp_path / "dummy_blueprint.py"
    blueprint_path.write_text("def main():\n    print('Hello from dummy blueprint')")
    
    # Use swarm_cli.add_blueprint to add the blueprint to the managed directory
    from swarm.extensions.launchers import swarm_cli
    test_args = ["swarm-cli", "add", str(blueprint_path)]
    monkeypatch.setattr(sys, "argv", test_args)
    swarm_cli.main()
    
    # Now, test installing the blueprint as a CLI utility
    test_args = ["swarm-cli", "install", "dummy_blueprint"]
    monkeypatch.setattr(sys, "argv", test_args)
    swarm_cli.main()
    
    # Capture and assert expected output
    captured = capsys.readouterr().out
    assert "Blueprint 'dummy_blueprint' installed as CLI utility 'dummy_blueprint' at:" in captured
    # Verify that the wrapper script exists
    wrapper_path = os.path.expanduser("~/.swarm/bin/dummy_blueprint")
    assert os.path.exists(wrapper_path)

def test_swarm_install_failure(monkeypatch, tmp_path, capsys):
    # Attempt to install a blueprint that has not been registered
    from swarm.extensions.launchers import swarm_cli
    test_args = ["swarm-cli", "install", "nonexistent_blueprint"]
    monkeypatch.setattr(sys, "argv", test_args)
    
    with pytest.raises(SystemExit):
        swarm_cli.main()
    
    captured = capsys.readouterr().out
    assert "Error: Blueprint 'nonexistent_blueprint' is not registered." in captured

def test_swarm_cli_creates_default_config(monkeypatch, tmp_path, capsys):
    # Create a dummy blueprint file with a main function
    blueprint_file = tmp_path / "dummy_blueprint.py"
    blueprint_file.write_text("def main():\n    print('Dummy blueprint executed')")
    
    # Set a temporary config path in tmp_path
    config_path = tmp_path / "swarm_config.json"
    if config_path.exists():
        config_path.unlink()
    
    # Import swarm_cli and monkey-patch run_blueprint to bypass actual blueprint execution
    from swarm.extensions.launchers import swarm_cli
    monkeypatch.setattr(swarm_cli, "run_blueprint", lambda name: None)
    
    # Set command line arguments for swarm_cli launcher with --config option using the 'run' command
    test_args = ["swarm-cli", "run", "dummy_blueprint", "--config", str(config_path)]
    monkeypatch.setattr(sys, "argv", test_args)
    
    # Run swarm_cli launcher
    swarm_cli.main()
    
    # Verify that the config file is created with the expected default config content
    assert config_path.exists(), "Default config file was not created."
    import json
    config_content = config_path.read_text()
    config_data = json.loads(config_content)
    expected_config = {"llm": {}, "mcpServers": {}}
    assert config_data == expected_config, "Default config content does not match expected."
    
    # Check output message
    captured = capsys.readouterr().out
    assert "Default config file created at:" in captured
