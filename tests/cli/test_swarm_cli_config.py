import os
import sys
import json
import pytest
from swarm.extensions.launchers import swarm_cli

def run_cli_with_args(args):
    sys.argv = args
    try:
        swarm_cli.main()
    except SystemExit:
        pass

def test_config_default_creation(tmp_path, monkeypatch, capsys):
    # Use a temporary config file in tmp_path
    config_path = tmp_path / "swarm_config.json"
    if config_path.exists():
        config_path.unlink()
    test_args = ["swarm-cli", "config", "list", "--section", "llm", "--config", str(config_path)]
    monkeypatch.setattr(sys, "argv", test_args)
    run_cli_with_args(sys.argv)
    captured = capsys.readouterr().out
    assert "Default config file created at:" in captured
    assert config_path.exists()
    with open(config_path, "r") as f:
        config = json.load(f)
    assert config == {"llm": {}, "mcpServers": {}}

def test_config_add_and_list(tmp_path, monkeypatch, capsys):
    config_path = tmp_path / "swarm_config.json"
    if config_path.exists():
        config_path.unlink()
    # Create default config file by triggering list command
    test_args = ["swarm-cli", "config", "list", "--section", "llm", "--config", str(config_path)]
    monkeypatch.setattr(sys, "argv", test_args)
    run_cli_with_args(sys.argv)
    _ = capsys.readouterr()
    
    # Add an entry to the llm section using --json
    entry = '{"provider": "test", "model": "test-model"}'
    test_args = ["swarm-cli", "config", "add", "--section", "llm", "--name", "test_entry", "--json", entry, "--config", str(config_path)]
    monkeypatch.setattr(sys, "argv", test_args)
    run_cli_with_args(sys.argv)
    
    # Verify by loading the config file directly
    with open(config_path, "r") as f:
        config = json.load(f)
    assert "test_entry" in config.get("llm", {}), "test_entry not found in llm section"
    assert config["llm"]["test_entry"]["provider"] == "test"

def test_config_remove(tmp_path, monkeypatch, capsys):
    config_path = tmp_path / "swarm_config.json"
    # Create default config and add an entry in mcpServers
    test_args = ["swarm-cli", "config", "list", "--section", "mcpServers", "--config", str(config_path)]
    monkeypatch.setattr(sys, "argv", test_args)
    run_cli_with_args(sys.argv)
    _ = capsys.readouterr()
    
    entry = '{"command": "test", "args": ["--test"]}'
    test_args = ["swarm-cli", "config", "add", "--section", "mcpServers", "--name", "test_mcp", "--json", entry, "--config", str(config_path)]
    monkeypatch.setattr(sys, "argv", test_args)
    run_cli_with_args(sys.argv)
    
    # Remove the entry from mcpServers
    test_args = ["swarm-cli", "config", "remove", "--section", "mcpServers", "--name", "test_mcp", "--config", str(config_path)]
    monkeypatch.setattr(sys, "argv", test_args)
    run_cli_with_args(sys.argv)
    
    # Load the config file and verify that 'test_mcp' key is removed.
    with open(config_path, "r") as f:
         updated_config = json.load(f)
    assert "test_mcp" not in updated_config.get("mcpServers", {}), "test_mcp entry should have been removed"