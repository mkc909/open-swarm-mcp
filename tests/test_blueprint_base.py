import pytest
from unittest.mock import MagicMock, patch
from swarm.extensions.blueprint.blueprint_base import BlueprintBase


# Mock subclass for testing BlueprintBase
class MockBlueprint(BlueprintBase):
    metadata = {
        "name": "mock_blueprint",
        "description": "A mock blueprint for testing.",
    }

    def register_blueprint_urls(self) -> None:
        pass

    def create_agents(self):
        agent1 = MagicMock(name="Agent1")
        agent1.instructions.return_value = "Agent 1 instructions"
        agent1.response_format = "text"
        agent2 = MagicMock(name="Agent2")
        agent2.instructions.return_value = "Agent 2 instructions"
        agent2.response_format = "text"
        return {
            "agent1": agent1,
            "agent2": agent2,
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

            def register_blueprint_urls(self) -> None:
                pass
        
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


def test_new_feature_configuration():
    """
    Test that new feature configuration parameters are set correctly during initialization.
    """
    mock_swarm = MagicMock()
    with patch("swarm.core.Swarm", return_value=mock_swarm):
        mock_config = {
            "llm": {
                "default": {
                    "model": "gpt-4o",
                    "api_key": "sk-mock-api-key-1234567890abcdef"
                }
            }
        }
        blueprint = MockBlueprint(
            config=mock_config,
            auto_complete_task=True,
            update_user_goal=True,
            update_user_goal_frequency=3
        )
        assert blueprint.auto_complete_task is True
        assert blueprint.update_user_goal is True
        assert blueprint.update_user_goal_frequency == 3


def test_is_task_done_yes():
    """
    Test that _is_task_done returns True when the LLM response starts with 'YES'.
    """
    mock_swarm = MagicMock()
    with patch("swarm.core.Swarm", return_value=mock_swarm):
        mock_config = {
            "llm": {
                "default": {
                    "model": "gpt-4o",
                    "api_key": "key"
                }
            }
        }
        blueprint = MockBlueprint(config=mock_config)
        # Patch the run_llm method to return a mock response with YES
        yes_response = MagicMock()
        yes_response.choices = [MagicMock(message={"content": "YES"})]
        blueprint.swarm.run_llm = MagicMock(return_value=yes_response)
        result = blueprint._is_task_done("goal", "summary", "last message")
        assert result is True


def test_is_task_done_no():
    """
    Test that _is_task_done returns False when the LLM response does not start with 'YES'.
    """
    mock_swarm = MagicMock()
    with patch("swarm.core.Swarm", return_value=mock_swarm):
        mock_config = {
            "llm": {
                "default": {
                    "model": "gpt-4o",
                    "api_key": "key"
                }
            }
        }
        blueprint = MockBlueprint(config=mock_config)
        no_response = MagicMock()
        no_response.choices = [MagicMock(message={"content": "NO"})]
        blueprint.swarm.run_llm = MagicMock(return_value=no_response)
        result = blueprint._is_task_done("goal", "summary", "last message")
        assert result is False


def test_update_user_goal():
    """
    Test that _update_user_goal updates the context variable 'user_goal' based on LLM response.
    """
    mock_swarm = MagicMock()
    with patch("swarm.core.Swarm", return_value=mock_swarm):
        mock_config = {
            "llm": {
                "default": {
                    "model": "gpt-4o",
                    "api_key": "key"
                }
            }
        }
        blueprint = MockBlueprint(config=mock_config)
        # Setup conversation messages list
        messages = [
            {"role": "user", "content": "I need help with testing."},
            {"role": "assistant", "content": "Sure, what do you need?"}
        ]
        # Patch run_llm to return a summary "new goal"
        summary_response = MagicMock()
        summary_response.choices = [MagicMock(message={"content": "new goal"})]
        blueprint.swarm.run_llm = MagicMock(return_value=summary_response)
        blueprint._update_user_goal(messages)
        assert blueprint.context_variables.get("user_goal") == "new goal"


@pytest.mark.timeout(1)
def test_autocompletion():
    """
    Test that autocompletion feature continues executing steps until task is complete.
    """
    mock_swarm = MagicMock()
    with patch("swarm.core.Swarm", return_value=mock_swarm), patch("builtins.input", return_value="exit"):
        mock_config = {
            "llm": {
                "default": {
                    "model": "gpt-4o",
                    "api_key": "sk-mock-api-key-1234567890abcdef"
                }
            }
        }
        blueprint = MockBlueprint(
            config=mock_config,
            auto_complete_task=True,
            update_user_goal=True,
            update_user_goal_frequency=3
        )
        # Set a starting agent
        blueprint.set_starting_agent(blueprint.create_agents()["agent1"])
        # Mock the run_llm and run methods to return a mock response with YES
        yes_response = MagicMock()
        yes_response.choices = [MagicMock(message={"content": "YES"})]
        blueprint.swarm.run_llm = MagicMock(return_value=yes_response)
        blueprint.swarm.run = MagicMock(return_value=yes_response)
        with patch.object(blueprint, "_is_task_done", return_value=True):
            blueprint.interactive_mode(stream=False)


def test_dynamic_user_goal_updates():
    """
    Test that dynamic user goal updates feature updates the user's goal based on LLM analysis.
    """
    mock_swarm = MagicMock()
    with patch("swarm.core.Swarm", return_value=mock_swarm):
        mock_config = {
            "llm": {
                "default": {
                    "model": "gpt-4o",
                    "api_key": "sk-mock-api-key-1234567890abcdef"
                }
            }
        }
        blueprint = MockBlueprint(
            config=mock_config,
            auto_complete_task=True,
            update_user_goal=True,
            update_user_goal_frequency=3
        )
        # Set a starting agent
        blueprint.set_starting_agent(blueprint.create_agents()["agent1"])
        # Mock the run_llm method to return a mock response with a new goal
        new_goal_response = MagicMock()
        new_goal_response.choices = [MagicMock(message={"content": "new goal"})]
        blueprint.swarm.run_llm = MagicMock(return_value=new_goal_response)
        blueprint._update_user_goal([{"role": "user", "content": "I need help with testing."}])
        assert blueprint.context_variables.get("user_goal") == "new goal"