# src/swarm/extensions/mcp/mcp_tool_provider.py

"""
MCPToolProvider Module for Open-Swarm

This module is responsible for discovering tools from MCP (Model Context Protocol) servers
and integrating them into the Open-Swarm framework as `Tool` instances. It handles
communication with MCP servers, constructs callable functions for dynamic tools, and
ensures that these tools are properly validated and integrated into the agent's function list.
"""

import logging
from typing import List, Dict, Any, Optional, Callable

from swarm.settings import DEBUG
from swarm.types import Tool, Agent  # Ensure `Agent` is correctly imported
from swarm.extensions.mcp.mcp_client import MCPClient  # Ensure correct import

# Initialize logger for this module
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG if DEBUG else logging.INFO)
stream_handler = logging.StreamHandler()
formatter = logging.Formatter("[%(levelname)s] %(asctime)s - %(name)s - %(message)s")
stream_handler.setFormatter(formatter)
if not logger.handlers:
    logger.addHandler(stream_handler)


class MCPToolProvider:
    """
    MCPToolProvider is responsible for discovering tools from an MCP server and converting
    them into `Tool` instances that can be utilized by agents within the Open-Swarm framework.
    """

    def __init__(self, server_name: str, server_config: dict):
        """
        Initialize an MCPToolProvider instance.

        Args:
            server_name (str): The name of the MCP server.
            server_config (dict): Configuration dictionary for the specific server.
        """
        self.server_name = server_name
        self.command = server_config.get("command", "npx")
        self.args = server_config.get("args", [])
        self.env = server_config.get("env", {})
        self.timeout = server_config.get("timeout", 30)
        self.client = MCPClient(
            command=self.command,
            args=self.args,
            env=self.env,
            timeout=self.timeout
        )
        logger.debug(
            f"Initialized MCPToolProvider for server '{self.server_name}' with config: {server_config}"
        )

    async def discover_tools(self, agent: Agent) -> List[Tool]:
        """
        Discover tools from the MCP server and return them as a list of `Tool` instances.

        Args:
            agent (Agent): The agent for which tools are being discovered.

        Returns:
            List[Tool]: A list of discovered `Tool` instances.

        Raises:
            RuntimeError: If tool discovery from the MCP server fails.
        """
        logger.debug(
            f"Starting tool discovery from MCP server '{self.server_name}' for agent '{agent.name}'."
        )
        try:
            # Use the get_tools method with caching
            tools = await self.client.get_tools(agent.name)
            logger.debug(
                f"Received tools from MCP server '{self.server_name}': {[tool.name for tool in tools]}"
            )

            # Since MCPClient already returns Tool objects with `func` assigned,
            # there's no need to recreate Tool instances here.
            # If additional processing is needed, it can be done here.

            return tools

        except Exception as e:
            logger.error(
                f"Failed to discover tools from MCP server '{self.server_name}': {e}",
                exc_info=True,
            )
            raise RuntimeError(
                f"Tool discovery failed for MCP server '{self.server_name}': {e}"
            ) from e

    # If additional functionalities are required, you can implement them here.
    # For example, merging tools from multiple MCP servers, filtering tools, etc.
