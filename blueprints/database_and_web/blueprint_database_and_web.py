"""
Database and Web Integration Blueprint

This blueprint integrates SQLite database querying with Brave Search capabilities.
It serves as a unified interface for combining database operations and web research tasks.
"""

import logging
import os
import traceback
from swarm.blueprint_base import BlueprintBase
from .sqlite_agent import SQLiteAgent
from .brave_agent import BraveAgent

logger = logging.getLogger(__name__)

class DatabaseAndWebBlueprint(BlueprintBase):
    """
    Blueprint integrating SQLite database querying and web search capabilities.
    """

    def __init__(self):
        """
        Initialize the DatabaseAndWebBlueprint with required metadata and agents.
        """
        self._metadata = {
            "title": "Database and Web Integration",
            "description": "Combines SQLite database querying with Brave Search capabilities.",
            "required_mcp_servers": ["sqlite", "brave-search"],
            "env_vars": ["SQLITE_DB_PATH", "BRAVE_API_KEY"],
        }
        self.sqlite_agent = SQLiteAgent()
        self.brave_agent = BraveAgent()
        logger.info("Initialized Database and Web Integration Blueprint.")

    @property
    def metadata(self):
        """
        Retrieve the blueprint's metadata.
        """
        return self._metadata

    def validate_env_vars(self):
        """
        Validate that required environment variables are set.
        """
        self.sqlite_agent.validate_env_vars()
        self.brave_agent.validate_env_vars()

    def get_agents(self):
        """
        Retrieve the dictionary of agents.

        Returns:
            dict: Dictionary containing all agents.
        """
        return {
            "SQLiteAgent": self.sqlite_agent.get_agent(),
            "BraveAgent": self.brave_agent.get_agent(),
        }

    def execute(self, config=None):
        """
        Execute the blueprint.

        Args:
            config (dict): Configuration dictionary.

        Returns:
            dict: Execution results.
        """
        try:
            self.validate_env_vars()
            agents = self.get_agents()
            logger.info(f"Agents available: {list(agents.keys())}")
            return {
                "status": "success",
                "messages": ["Database and Web Integration Blueprint executed successfully."],
                "metadata": self.metadata,
            }
        except Exception as e:
            logger.error(f"Error executing blueprint: {e}")
            traceback.print_exc()
            return {
                "status": "failure",
                "messages": [str(e)],
                "metadata": self.metadata,
            }

if __name__ == "__main__":
    blueprint = DatabaseAndWebBlueprint()
    print(blueprint.execute())
