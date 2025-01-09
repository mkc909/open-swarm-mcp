"""
Database and Web Integration Blueprint

This blueprint integrates SQLite database querying with Brave Search capabilities.
"""

import logging
from typing import List, Dict, Callable, Any

from swarm.extensions.blueprint import BlueprintBase
from swarm.types import Agent

# Configure logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
if not logger.handlers:
    stream_handler = logging.StreamHandler()
    formatter = logging.Formatter("[%(levelname)s] %(asctime)s - %(name)s - %(message)s")
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)


class DatabaseAndWebBlueprint(BlueprintBase):
    """
    Blueprint integrating SQLite database querying and web search capabilities.
    """

    @property
    def metadata(self) -> Dict[str, Any]:
        """
        Define metadata for the blueprint, including title, description,
        required MCP servers, and environment variables.
        """
        return {
            "title": "Database and Web Integration",
            "description": "Combines SQLite database querying with Brave Search capabilities.",
            "required_mcp_servers": ["sqlite", "brave-search"],
            "env_vars": ["SQLITE_DB_PATH", "BRAVE_API_KEY"],
        }

    def create_agents(self) -> Dict[str, Agent]:
        """
        Create agents for this blueprint, defining their instructions,
        MCP servers, required environment variables, and transfer functions.

        Returns:
            Dict[str, Agent]: Dictionary containing all created agents.
        """
        import os

        # Retrieve environment variables
        sqlite_db_path = os.getenv("SQLITE_DB_PATH")
        if not sqlite_db_path:
            raise EnvironmentError("Environment variable 'SQLITE_DB_PATH' is not set.")

        brave_api_key = os.getenv("BRAVE_API_KEY")
        if not brave_api_key:
            raise EnvironmentError("Environment variable 'BRAVE_API_KEY' is not set.")

        # Define agents dictionary
        agents = {}

        # Define transfer functions
        def transfer_to_brave_search() -> Agent:
            """
            Transfer control from SQLiteAgent to BraveSearchAgent.
            """
            logger.debug("Transferring control from SQLiteAgent to BraveSearchAgent.")
            return agents["BraveSearchAgent"]

        def transfer_to_sqlite() -> Agent:
            """
            Transfer control from BraveSearchAgent to SQLiteAgent.
            """
            logger.debug("Transferring control from BraveSearchAgent to SQLiteAgent.")
            return agents["SQLiteAgent"]

        # SQLite Agent
        sqlite_agent = Agent(
            name="SQLiteAgent",
            instructions="You are a SQLite expert. Perform efficient database queries and provide clear results.",
            mcp_servers=["sqlite"],
            env_vars={"SQLITE_DB_PATH": sqlite_db_path},
            functions=[transfer_to_brave_search],
        )

        # Brave Search Agent
        brave_search_agent = Agent(
            name="BraveSearchAgent",
            instructions="You are a web search assistant. Use Brave Search to provide accurate and relevant web results.",
            mcp_servers=["brave-search"],
            env_vars={"BRAVE_API_KEY": brave_api_key},
            functions=[transfer_to_sqlite],
        )

        # Populate agents dictionary
        agents["SQLiteAgent"] = sqlite_agent
        agents["BraveSearchAgent"] = brave_search_agent

        logger.info("SQLiteAgent and BraveSearchAgent have been created.")
        self.set_starting_agent(sqlite_agent)  # Set SQLiteAgent as the starting agent
        return agents


if __name__ == "__main__":
    DatabaseAndWebBlueprint.main()
