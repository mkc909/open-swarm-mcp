# examples/basic-bare_minimum/run.py

"""
Bare Minimum Example

Original Example:
This example is adapted from the official OpenAI Swarm project.
Refactored to fit the Open Swarm MCP framework.
For more information, visit: https://github.com/matthewhand/open-swarm-mcp 
"""

from swarm import Swarm, Agent

def run_example():
    client = Swarm()

    agent = Agent(
        name="Agent",
        instructions="You are a helpful agent.",
    )

    messages = [{"role": "user", "content": "Hi!"}]
    response = client.run(agent=agent, messages=messages)

    print(response.messages[-1]["content"])
