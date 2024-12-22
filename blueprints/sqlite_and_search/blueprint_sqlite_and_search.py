# blueprints/sqlite_and_search/blueprint_sqlite_and_search.py

"""
SQLite and Search Integration Example

Original Example:
This example is adapted from the official OpenAI Swarm project.
Refactored to fit the Open Swarm MCP framework.
For more information, visit: https://github.com/matthewhand/open-swarm-mcp 
"""

from swarm import Swarm, Agent

EXAMPLE_METADATA = {
    "title": "SQLite and Search Integration",
    "description": "Integrates SQLite database querying with search capabilities via MCP servers.",
    "required_mcp_servers": ["sqlite"],
    "env_vars": ["SQLITE_DB_PATH"]
}

def run_example():
    client = Swarm()

    agent = Agent(
        name="SQLiteSearchAgent",
        instructions="You can query the SQLite database and perform searches.",
    )

    messages = [{"role": "user", "content": "Find all users in the database."}]
    response = client.run(agent=agent, messages=messages)

    print(response.messages[-1]["content"])
