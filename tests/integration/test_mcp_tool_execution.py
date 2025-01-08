"""
Integration tests for MCP tool execution from the blueprint filesystem.
"""

import pytest
from subprocess import run
from pathlib import Path


@pytest.fixture
def setup_tool_execution(tmp_path):
    """Set up a temporary blueprint filesystem with an executable tool."""
    tools_dir = tmp_path / "blueprints" / "test_blueprint" / "tools"
    tools_dir.mkdir(parents=True)

    # Create a mock tool
    mock_tool = tools_dir / "mock_tool"
    mock_tool.write_text("#!/bin/bash\necho 'Tool executed successfully'\n")
    mock_tool.chmod(0o755)

    return tmp_path


def test_execute_tool(setup_tool_execution):
    """Test execution of a tool from the filesystem."""
    tool_path = setup_tool_execution / "blueprints" / "test_blueprint" / "tools" / "mock_tool"
    result = run([tool_path], capture_output=True, text=True, check=True)
    assert result.stdout.strip() == "Tool executed successfully"
