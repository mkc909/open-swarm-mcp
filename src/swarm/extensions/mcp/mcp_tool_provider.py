'''extensions/mcp_tool_provider.py'''

"""
MCPToolProvider Module for Open-Swarm

This module is responsible for discovering tools from MCP (Model Context Protocol) servers
and integrating them into the Open-Swarm framework as `Tool` instances. It handles
communication with MCP servers, constructs callable functions for dynamic tools, and
ensures that these tools are properly validated and integrated into the agent's function list.
"""

import logging
import json
from typing import List, Dict, Any, Optional, Callable
import asyncio

from swarm.types import Tool
from swarm.extensions.mcp.mcp_client import MCPClient  # Assuming MCPClient handles JSON-RPC or REST calls

# Initialize logger for this module
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
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
        self.config = server_config
        self.client = None
        self.initialize_client()
        logger.debug(f"Initialized MCPToolProvider for server '{self.server_name}' with config: {server_config}")

    async def discover_tools(self, agent: 'Agent') -> List[Tool]:
        """
        Discover tools from the MCP server and return them as a list of `Tool` instances.

        Args:
            agent (Agent): The agent for which tools are being discovered.

        Returns:
            List[Tool]: A list of discovered `Tool` instances.

        Raises:
            RuntimeError: If tool discovery from the MCP server fails.
        """
        logger.info(f"Starting tool discovery from MCP server '{self.server_name}' for agent '{agent.name}'.")
        try:
            # Fetch tool metadata from the MCP server
            tools_metadata = await self.client.get_tools(agent.name)
            logger.debug(f"Received tools metadata from MCP server '{self.server_name}': {tools_metadata}")

            tools = []
            for tool_meta in tools_metadata:
                tool_name = tool_meta.get("name")
                tool_description = tool_meta.get("description", "")
                input_schema = tool_meta.get("input_schema", {})

                if not tool_name:
                    logger.warning(f"Tool metadata missing 'name' field: {tool_meta}")
                    continue  # Skip tools without a name

                # Create a callable function that routes the call to the MCP server
                func = self._create_dynamic_tool_func(tool_meta)

                # Instantiate the Tool with dynamic=True
                tool = Tool(
                    name=tool_name,
                    func=func,
                    description=tool_description,
                    input_schema=input_schema,
                    dynamic=True
                )
                logger.debug(f"Created dynamic Tool instance: {tool.name}")
                tools.append(tool)

            logger.info(f"Discovered {len(tools)} tools from MCP server '{self.server_name}' for agent '{agent.name}'.")
            return tools

        except Exception as e:
            logger.error(f"Failed to discover tools from MCP server '{self.server_name}': {e}", exc_info=True)
            raise RuntimeError(f"Tool discovery failed for MCP server '{self.server_name}': {e}") from e

    def _create_dynamic_tool_func(self, tool_meta: Dict[str, Any]) -> Callable:
        """
        Create a callable function that routes execution to the MCP server for a given tool.

        Args:
            tool_meta (Dict[str, Any]): Metadata dictionary for the tool.

        Returns:
            Callable: A function that executes the tool via the MCP server.
        """

        async def dynamic_tool_func(**kwargs) -> Any:
            """
            Dynamic tool execution function that forwards the call to the MCP server.

            Args:
                **kwargs: Keyword arguments representing the tool's input parameters.

            Returns:
                Any: The result returned by the MCP server.

            Raises:
                RuntimeError: If the MCP server call fails.
            """
            logger.debug(f"Executing dynamic tool '{tool_meta.get('name')}' with arguments: {kwargs}")

            # Validate input against the input_schema if necessary
            # (Assuming validation is handled elsewhere or via the MCP server)

            try:
                # Make the call to the MCP server's tool execution endpoint
                response = await self.client.execute_tool(tool_meta.get("name"), kwargs)
                logger.debug(f"Received response from MCP server for tool '{tool_meta.get('name')}': {response}")
                return response
            except Exception as e:
                logger.error(f"Error executing dynamic tool '{tool_meta.get('name')}' on MCP server '{self.server_name}': {e}", exc_info=True)
                raise RuntimeError(f"Execution of tool '{tool_meta.get('name')}' failed: {e}") from e

        # If the execution needs to be synchronous, wrap the async function
        def sync_dynamic_tool_func(**kwargs) -> Any:
            """
            Synchronous wrapper for the dynamic tool execution function.

            Args:
                **kwargs: Keyword arguments representing the tool's input parameters.

            Returns:
                Any: The result returned by the MCP server.

            Raises:
                RuntimeError: If the MCP server call fails.
            """
            return asyncio.run(dynamic_tool_func(**kwargs))

        # Return the appropriate callable based on your application's async handling
        return sync_dynamic_tool_func

