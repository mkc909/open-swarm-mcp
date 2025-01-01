"""
Brave Search Agent

This agent provides capabilities for performing web searches using the Brave Search MCP server.
"""

import logging
from swarm import Agent

logger = logging.getLogger(__name__)

class BraveAgent:
    """
    Agent for performing web searches via the Brave Search MCP server.
    """

    def __init__(self):
        """
        Initialize the BraveAgent.
        """
        self._agent = Agent(
            name="BraveAgent",
            instructions="You can perform web searches using the Brave Search tool.",
            functions=[self.perform_search],
            parallel_tool_calls=True,
        )
        logger.info("Initialized BraveAgent.")

    def validate_env_vars(self):
        """
        Validate that the BRAVE_API_KEY environment variable is set.
        """
        brave_api_key = os.getenv("BRAVE_API_KEY")
        if not brave_api_key:
            logger.error("Environment variable BRAVE_API_KEY is not set.")
            raise ValueError("Environment variable BRAVE_API_KEY is not set.")
        logger.info("Validated BRAVE_API_KEY environment variable.")

    def perform_search(self, query: str) -> str:
        """
        Perform a web search using the Brave Search MCP server.

        Args:
            query (str): The search query.

        Returns:
            str: Search results or an error message.
        """
        logger.debug(f"Performing web search for query: '{query}'.")
        # Add Brave Search MCP server integration logic here
        return f"Performed web search for '{query}' successfully."

    def get_agent(self) -> Agent:
        """
        Retrieve the BraveAgent instance.

        Returns:
            Agent: The BraveAgent instance.
        """
        return self._agent
