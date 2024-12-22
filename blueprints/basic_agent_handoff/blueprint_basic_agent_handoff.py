# examples/basic-agent_handoff/run.py

"""
Agent Handoff Example

Original Example:
This example is adapted from the official OpenAI Swarm project.
Refactored to fit the Open Swarm MCP framework.
For more information, visit: https://github.com/matthewhand/open-swarm-mcp 
"""

from swarm import Swarm, Agent

def run_example():
    client = Swarm()

    english_agent = Agent(
        name="English Agent",
        instructions="You only speak English.",
    )

    spanish_agent = Agent(
        name="Spanish Agent",
        instructions="You only speak Spanish.",
    )

    def transfer_to_spanish_agent():
        """Transfer Spanish speaking users immediately."""
        return spanish_agent

    english_agent.functions.append(transfer_to_spanish_agent)

    messages = [{"role": "user", "content": "Hola. ¿Cómo estás?"}]
    response = client.run(agent=english_agent, messages=messages)

    print(response.messages[-1]["content"])
