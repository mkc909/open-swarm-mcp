import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from swarm.extensions.blueprint.blueprint_base import BlueprintBase


class MockBlueprint(BlueprintBase):
    """
    A mock implementation of BlueprintBase for testing purposes.
    """
    metadata = {
        "name": "mock_blueprint",
        "description": "A mock blueprint for testing purposes.",
    }

    def create_agents(self):
        """
        Returns a dictionary of mock agents.
        """
        return {"agent1": MagicMock(name="Agent1"), "agent2": MagicMock(name="Agent2")}


@patch("swarm.extensions.blueprint.blueprint_base.Swarm", autospec=True)
def test_blueprint_base_initialization(mock_swarm_class):
    """
    Test that BlueprintBase initializes correctly with a mocked Swarm instance.
    """
    # Mock Swarm
    mock_swarm = MagicMock()
    mock_swarm_class.return_value = mock_swarm

    # Initialize blueprint
    blueprint = MockBlueprint(config_path="mock_config.json")

    # Validate initialization
    assert blueprint.swarm == mock_swarm, "Blueprint should store the mocked Swarm instance."
    assert blueprint.metadata["name"] == "mock_blueprint", "Metadata should match subclass definition."
    assert isinstance(blueprint.create_agents(), dict), "Agents should be returned as a dictionary."


def test_metadata_enforcement():
    """
    Test that a BlueprintBase subclass must define metadata.
    """
    with patch("swarm.extensions.blueprint.blueprint_base.Swarm", autospec=True):
        class InvalidBlueprint(BlueprintBase):
            metadata = None  # Invalid metadata definition

            def create_agents(self):
                return {"invalid_agent": MagicMock(name="InvalidAgent")}

        # Assert that metadata enforcement raises an error
        with pytest.raises(AssertionError, match="Blueprint metadata must be defined and must be a dictionary."):
            InvalidBlueprint(config_path="mock_config.json")


@patch("swarm.extensions.blueprint.blueprint_base.Swarm", autospec=True)
def test_create_agents(mock_swarm_class):
    """
    Test that create_agents returns a dictionary of agents.
    """
    # Mock Swarm
    mock_swarm = MagicMock()
    mock_swarm_class.return_value = mock_swarm

    # Initialize blueprint
    blueprint = MockBlueprint(config_path="mock_config.json")

    # Validate agent creation
    agents = blueprint.create_agents()
    assert isinstance(agents, dict), "Agents should be returned as a dictionary."
    assert "agent1" in agents and "agent2" in agents, "Expected agents are missing."

# @patch("swarm.extensions.blueprint.blueprint_base.Swarm", autospec=True)
# def test_interactive_mode(mock_swarm_class, monkeypatch):
#     """
#     Test the synchronous interactive mode with agents having a `.name` attribute.
#     """
#     # Mock Swarm and agents
#     mock_swarm = MagicMock()
#     mock_swarm_class.return_value = mock_swarm

#     # Create mock agents with a `.name` attribute
#     primary_agent = MagicMock()
#     primary_agent.name = "PrimaryAgent"

#     mock_agent1 = MagicMock()
#     mock_agent1.name = "Agent1"

#     mock_agent2 = MagicMock()
#     mock_agent2.name = "Agent2"

#     # Assign agents to the mock Swarm
#     mock_swarm.agents = {
#         "PrimaryAgent": primary_agent,
#         "Agent1": mock_agent1,
#         "Agent2": mock_agent2,
#     }

#     # Mock asynchronous tool discovery
#     mock_swarm.discover_and_merge_agent_tools = AsyncMock(return_value=[])

#     # Mock Swarm's `run` method with a JSON-serializable response
#     mock_response = MagicMock()
#     mock_response.messages = [{"content": "Mocked interactive response"}]
#     mock_swarm.run.return_value = mock_response

#     # Simulate user input
#     prompts = ["mock prompt", "exit"]
#     responses = iter(prompts)
#     monkeypatch.setattr("builtins.input", lambda _: next(responses))

#     # Initialize blueprint and set starting agent
#     blueprint = MockBlueprint(config_path="mock_config.json")
#     blueprint.set_starting_agent(mock_swarm.agents["PrimaryAgent"])

#     # Run interactive mode
#     blueprint.interactive_mode()

#     # Validate Swarm.run was called with the correct agent and messages
#     mock_swarm.run.assert_called_once_with(
#         agent=mock_swarm.agents["PrimaryAgent"], messages=[]
#     )
