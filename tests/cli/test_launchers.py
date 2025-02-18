import os
import sys
import pytest  # type: ignore

def test_swarm_install_creates_executable(monkeypatch, tmp_path, capsys):
    # Create a dummy blueprint file
    blueprint_path = tmp_path / "dummy_blueprint.py"
    blueprint_path.write_text("def main():\n    print('Hello from dummy blueprint')")
    
    # Monkey-patch build_executable to simulate successful executable creation
    from launchers import build_launchers
    def fake_build_executable(blueprint, output):
        assert blueprint == str(blueprint_path)
        return os.path.join(str(output), "dummy_executable")
    monkeypatch.setattr(build_launchers, "build_executable", fake_build_executable)
    
    # Set command line arguments for swarm_install
    from launchers import swarm_install
    test_args = ["swarm-install", str(blueprint_path), "--output", str(tmp_path)]
    monkeypatch.setattr(sys, "argv", test_args)
    
    # Run swarm_install launcher
    swarm_install.main()
    
    # Capture and assert expected output
    captured = capsys.readouterr().out
    assert "Successfully created standalone utility at:" in captured
    assert "dummy_executable" in captured

def test_swarm_install_failure(monkeypatch, tmp_path, capsys):
    # Create a dummy blueprint file
    blueprint_path = tmp_path / "dummy_blueprint.py"
    blueprint_path.write_text("def main():\n    print('Hello')")
    
    # Monkey-patch build_executable to simulate failure (returning None)
    from launchers import build_launchers
    def fake_build_executable_fail(blueprint, output):
        return None
    monkeypatch.setattr(build_launchers, "build_executable", fake_build_executable_fail)
    
    # Set command line arguments for swarm_install
    from launchers import swarm_install
    test_args = ["swarm-install", str(blueprint_path), "--output", str(tmp_path)]
    monkeypatch.setattr(sys, "argv", test_args)
    
    # Expect the launcher to exit on failure
    with pytest.raises(SystemExit):
        swarm_install.main()
    
    # Capture and assert the failure message
    captured = capsys.readouterr().out
    assert "Failed to create standalone utility" in captured
def test_swarm_cli_creates_default_config(monkeypatch, tmp_path, capsys):
    # Create a dummy blueprint file with a main function.
    blueprint_file = tmp_path / "dummy_blueprint.py"
    blueprint_file.write_text("def main():\n    print('Dummy blueprint executed')")
    
    # Set a temporary config path in tmp_path.
    config_path = tmp_path / "swarm_config.json"
    if config_path.exists():
        config_path.unlink()
    
    # Set command line arguments for swarm_cli launcher with --config option.
    from launchers import swarm_cli
    test_args = ["swarm-cli", str(blueprint_file), "--config", str(config_path)]
    monkeypatch.setattr(sys, "argv", test_args)
    
    # Run swarm_cli launcher.
    swarm_cli.main()
    
    # Verify that the config file is created with the expected default config content.
    assert config_path.exists(), "Default config file was not created."
    config_content = config_path.read_text()
    expected_config = '''{
    "llm": {
        "default": {
            "provider": "openai",
            "model": "gpt-4o",
            "base_url": "https://api.openai.com/v1",
            "api_key": "${OPENAI_API_KEY}"
        }
    },
    "mcpServers": {
        "everything": {
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-everything"],
            "env": {}
        }
    }
}'''
    assert config_content.strip() == expected_config.strip(), "Default config content does not match expected."
    
    # Check output message.
    captured = capsys.readouterr().out
    assert "Default config file created at:" in captured