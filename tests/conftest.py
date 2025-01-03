import os
import shutil
from pathlib import Path
from dotenv import load_dotenv
import pytest
from unittest.mock import patch

# Load environment variables immediately upon importing conftest.py
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

def pytest_configure():
    """
    Pytest configuration hook to set up the testing environment.
    """
    # Copy swarm_config.json to the temporary testing directory
    config_file = Path(__file__).parent.parent / "swarm_config.json"
    if config_file.exists():
        test_config_path = Path(__file__).parent / "swarm_config.json"
        shutil.copy(config_file, test_config_path)
        print(f"Copied {config_file} to {test_config_path}")
        # Debug: Verify the file exists in the test directory
        if Path(test_config_path).exists():
            print(f"Verified: {test_config_path} exists.")
        else:
            print(f"Error: {test_config_path} does not exist.")
    else:
        print(f"Warning: {config_file} not found. Tests may fail if a configuration file is required.")

@pytest.fixture
def mock_env():
    """Fixture to set up mock environment variables."""
    with patch.dict(os.environ, {"TEST_VAR": "test_value", "EMPTY_VAR": ""}):
        yield

@pytest.fixture
def valid_config():
    """Provide a valid configuration dictionary."""
    return {
        "llm_providers": {
            "default": {"provider": "mock", "api_key": "${TEST_VAR}"}
        },
        "mcpServers": {
            "example": {"env": {"EXAMPLE_VAR": "${TEST_VAR}"}}
        },
    }
