# blueprints/sqlite_and_search/blueprint_sqlite_and_search.py

"""
SQLite and Search Integration Blueprint

This blueprint integrates SQLite database querying with search capabilities via MCP servers.
"""

import os
from typing import Dict, Any, Optional
from swarm import Agent
from open_swarm_mcp.blueprint_base import BlueprintBase

class SQLiteSearchBlueprint(BlueprintBase):
    """
    SQLite and Search Integration Blueprint Implementation.
    """

    def __init__(self):
        super().__init__()
        self._metadata = {
            "title": "SQLite and Search Integration",
            "description": "Integrates SQLite database querying with search capabilities via MCP servers.",
            "required_mcp_servers": ["sqlite"],
            "env_vars": ["SQLITE_DB_PATH"]
        }

    @property
    def metadata(self) -> Dict[str, Any]:
        return self._metadata

    def validate_env_vars(self) -> None:
        """Validate that required environment variables are set and directories exist."""
        sqlite_db_path = os.getenv("SQLITE_DB_PATH")
        if not sqlite_db_path:
            raise ValueError("Environment variable SQLITE_DB_PATH is not set.")

        if not os.path.exists(sqlite_db_path):
            raise ValueError(f"SQLite database file does not exist at: {sqlite_db_path}")

    def create_agent(self) -> Agent:
        """Create and configure the SQLite and Search agent."""
        return Agent(
            name="SQLiteSearchAgent",
            instructions="""You can query the SQLite database and perform searches.
Please ensure that all operations are within the allowed parameters.""",
            functions=[],
            # tool_choice=None,
            parallel_tool_calls=True
        )

    def execute(self, config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute the blueprint in framework integration mode.

        Args:
            config (Optional[Dict[str, Any]]): Configuration dictionary from the framework.

        Returns:
            Dict[str, Any]: Execution results containing status, messages, and metadata.
        """
        self.validate_env_vars()
        agent = self.create_agent()

        # Allow for message override from framework config
        default_message = {
            "role": "user",
            "content": "Find all users in the database."
        }
        messages = config.get('messages', [default_message]) if config else [default_message]

        response = self.client.run(agent=agent, messages=messages)

        return {
            "status": "success",
            "messages": response.messages,
            "metadata": self.metadata
        }

# Entry point for standalone execution
if __name__ == "__main__":
    blueprint = SQLiteSearchBlueprint()
    try:
        blueprint.interactive_mode()
    except Exception as e:
        print(f"Error running SQLite and Search Blueprint: {e}")
