import pytest
from unittest.mock import MagicMock, patch
from swarm.extensions.blueprint.blueprint_base import BlueprintBase


# Mock subclass for testing BlueprintBase
class MockBlueprint(BlueprintBase):
    metadata = {
        "name": "mock_blueprint",
        "description": "A mock blueprint for testing.",
    }

    def create_agents(self):
        return {
            "agent1": MagicMock(name="Agent1"),
            "agent2": MagicMock(name="Agent2"),
        }


def test_blueprint_base_initialization():
    """
    Test that BlueprintBase initializes correctly with a mocked Swarm instance.
    """
    # Mock Swarm
    mock_swarm = MagicMock()

    # Patch the Swarm class to return the mocked Swarm instance
    with patch("swarm.core.Swarm", return_value=mock_swarm):
        # Mock configuration with a valid API key for the 'default' LLM profile
        mock_config = {
            "llm": {
                "default": {
                    "model": "gpt-4o",
                    "api_key": "sk-mock-api-key-1234567890abcdef"  # Add a valid API key
                }
            }
        }

        # Initialize blueprint
        blueprint = MockBlueprint(config=mock_config)

        # Validate initialization
        assert blueprint.metadata["name"] == "mock_blueprint", "Metadata should match subclass definition."
        assert isinstance(blueprint.create_agents(), dict), "Agents should be returned as a dictionary."

def test_metadata_enforcement():
    """
    Test that a BlueprintBase subclass must define metadata.
    """
    with patch("swarm.core.Swarm", autospec=True):
        class InvalidBlueprint(BlueprintBase):
            metadata = None  # Invalid metadata definition

            def create_agents(self):
                return {"invalid_agent": MagicMock(name="InvalidAgent")}

        # Mock configuration with a valid API key for the 'default' LLM profile
        mock_config = {
            "llm": {
                "default": {
                    "model": "gpt-4o",
                    "api_key": "sk-mock-api-key-1234567890abcdef"  # Add a valid API key
                }
            }
        }

        # Assert that metadata enforcement raises an error
        with pytest.raises(AssertionError, match="Blueprint metadata must be defined and must be a dictionary."):
            InvalidBlueprint(config=mock_config)


@patch("swarm.core.Swarm", autospec=True)
def test_create_agents(mock_swarm_class):
    """
    Test that create_agents returns a dictionary of agents.
    """
    # Mock Swarm
    mock_swarm = MagicMock()
    mock_swarm_class.return_value = mock_swarm

    # Mock configuration with a valid API key for the 'default' LLM profile
    mock_config = {
        "llm": {
            "default": {
                "model": "gpt-4o",
                "api_key": "sk-mock-api-key-1234567890abcdef"  # Add a valid API key
            }
        }
    }

    # Initialize blueprint
    blueprint = MockBlueprint(config=mock_config)

    # Validate agent creation
    agents = blueprint.create_agents()
    assert isinstance(agents, dict), "Agents should be returned as a dictionary."
    assert "agent1" in agents and "agent2" in agents, "Expected agents are missing."