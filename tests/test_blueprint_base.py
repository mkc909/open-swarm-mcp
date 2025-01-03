import pytest
from unittest.mock import MagicMock, patch
from swarm.extensions.blueprint.blueprint_base import BlueprintBase


class MockBlueprint(BlueprintBase):
    """
    A mock implementation of BlueprintBase for testing purposes.
    """
    metadata = {
        "name": "mock_blueprint",
        "description": "A mock blueprint for testing purposes."
    }

    def create_agents(self):
        return ["agent1", "agent2"]


@patch("swarm.extensions.blueprint.blueprint_base.Swarm", autospec=True)
def test_blueprint_base_initialization(mock_swarm_class):
    """
    Test that BlueprintBase initializes correctly with a mocked Swarm instance.
    """
    # Mock the Swarm instance
    mock_swarm = MagicMock()
    mock_swarm_class.return_value = mock_swarm

    # Initialize the blueprint
    blueprint = MockBlueprint(config_path="mock_config.json")

    # Assertions
    assert blueprint.swarm == mock_swarm, "Blueprint should store the mocked Swarm instance."
    assert blueprint.metadata["name"] == "mock_blueprint", "Metadata should match subclass definition."

def test_metadata_enforcement():
    """
    Test that a BlueprintBase subclass must define metadata.
    """
    with patch("swarm.extensions.blueprint.blueprint_base.Swarm", autospec=True):
        class InvalidBlueprint(BlueprintBase):
            metadata = None  # Incomplete metadata triggers the assertion

            def create_agents(self):
                return ["mock_agent"]

        with pytest.raises(AssertionError, match="Blueprint metadata must be defined"):
            InvalidBlueprint(config_path="mock_config.json")

@patch("swarm.extensions.blueprint.blueprint_base.Swarm", autospec=True)
def test_create_agents(mock_swarm_class):
    """
    Test that create_agents is called and returns expected agents.
    """
    # Mock the Swarm instance
    mock_swarm = MagicMock()
    mock_swarm_class.return_value = mock_swarm

    # Initialize the blueprint
    blueprint = MockBlueprint(config_path="mock_config.json")

    # Call create_agents and validate the output
    agents = blueprint.create_agents()
    assert agents == ["agent1", "agent2"], "Agents returned by create_agents should match the subclass implementation."

@patch("swarm.extensions.blueprint.blueprint_base.Swarm", autospec=True)
def test_interactive_mode(mock_swarm_class, monkeypatch):
    """
    Test the synchronous interactive mode.
    """
    # Mock the Swarm instance and its methods
    mock_swarm = MagicMock()
    mock_swarm_class.return_value = mock_swarm

    # Mock agents and their behavior
    mock_swarm.agents = {"PrimaryAgent": MagicMock()}
    mock_response = MagicMock()
    mock_response.messages = [{"content": "mocked response"}]
    mock_swarm.run.return_value = mock_response

    # Mock user input
    prompts = ["prompt1", "exit"]
    responses = iter(prompts)
    monkeypatch.setattr("builtins.input", lambda _: next(responses))

    # Initialize the blueprint
    blueprint = MockBlueprint(config_path="mock_config.json")

    # Run interactive_mode
    blueprint.interactive_mode()

    # Validate that Swarm.run was called with the correct agent and input
    mock_swarm.run.assert_called_once_with(
        agent=mock_swarm.agents["PrimaryAgent"],
        messages=[]
    )
