import pytest
from swarm.extensions.blueprint.blueprint_base import BlueprintBase

# Dummy agent for testing purposes
class DummyAgent:
    def __init__(self, name):
        self.name = name

# A minimal concrete implementation of BlueprintBase for testing
class FakeBlueprint(BlueprintBase):
    @property
    def metadata(self):
        # Provide minimal metadata with no required environment variables
        return {"env_vars": []}
    
    def create_agents(self):
        # Return an empty dictionary; agents will be manually added in tests if needed
        return {}

    def set_starting_agent(self, agent):
        self.starting_agent = agent
        self.context_variables = {"active_agent_name": agent.name}

    def determine_active_agent(self):
        return self.starting_agent

def test_set_and_determine_active_agent():
    # Instantiate the FakeBlueprint with an empty config including dummy llm config
    blueprint = FakeBlueprint(config={"llm": {"default": {"dummy": "dummy"}}})
    # Create a dummy agent
    dummy_agent = DummyAgent("agent1")
    # Set the starting agent
    blueprint.set_starting_agent(dummy_agent)
    # Verify that starting_agent and context_variables are correctly set
    assert blueprint.starting_agent == dummy_agent
    assert blueprint.context_variables.get("active_agent_name") == "agent1"
    # Verify that determine_active_agent returns the correct agent
    active_agent = blueprint.determine_active_agent()
    assert active_agent == dummy_agent

def test_run_with_context():
    # Create a dummy agent
    dummy_agent = DummyAgent("agent1")
    blueprint = FakeBlueprint(config={"llm": {"default": {"dummy": "dummy"}}})
    blueprint.set_starting_agent(dummy_agent)
    
    # Create fake response and swarm objects
    class FakeResponse:
        def __init__(self, messages, agent):
            self.messages = messages
            self.agent = agent

    class FakeSwarm:
        def __init__(self, agent):
            self.agents = {agent.name: agent}
        def run(self, agent, messages, context_variables, stream, debug):
            return FakeResponse(messages + [{"role": "assistant", "content": "Test Completed", "sender": agent.name}], agent)
    
    blueprint.swarm = FakeSwarm(dummy_agent)
    messages = [{"role": "user", "content": "Hello"}]
    context = {"foo": "bar"}
    result = blueprint.run_with_context(messages, context)
    # Check that the returned response has assistant message appended
    assert "Test Completed" in result["response"].messages[-1]["content"]
    # Check that context_variables include active_agent_name equal to dummy_agent.name
    assert result["context_variables"]["active_agent_name"] == dummy_agent.name