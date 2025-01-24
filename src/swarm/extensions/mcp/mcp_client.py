import asyncio
import logging
import os
from typing import Any, Dict, List, Callable

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from swarm.types import Tool

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class MCPClient:
    """Manages connections and interactions with MCP servers using the MCP Python SDK."""

    def __init__(self, server_config: Dict[str, Any], timeout: int = 30):
        """
        Initialize the MCPClient with server configuration.

        Args:
            server_config (dict): Configuration dictionary for the MCP server.
            timeout (int): Timeout for operations in seconds.
        """
        self.command = server_config.get("command", "npx")
        self.args = server_config.get("args", [])
        self.env = {**os.environ.copy(), **server_config.get("env", {})}
        self.timeout = timeout

        logger.info(f"Initialized MCPClient with command={self.command}, args={self.args}")

    async def _create_session(self):
        """
        Create and initialize a new MCP session within a context manager.
        """
        logger.debug("Creating a new MCP session...")
        server_params = StdioServerParameters(
            command=self.command, args=self.args, env=self.env
        )
        try:
            async with stdio_client(server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    logger.info("MCP session initialized successfully.")
                    return session
        except Exception as e:
            logger.error(f"Failed to initialize MCP session: {e}")
            raise RuntimeError("Session initialization failed.") from e

    async def list_tools(self) -> List[Tool]:
        """
        Discover tools from the MCP server within a session context.

        Returns:
            List[Tool]: A list of discovered tools.
        """
        server_params = StdioServerParameters(
            command=self.command, args=self.args, env=self.env
        )
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                try:
                    logger.info("Requesting tool list from MCP server...")
                    tools_response = await session.list_tools()

                    tools = [
                        Tool(
                            name=tool.name,
                            description=tool.description,
                            input_schema=tool.inputSchema,
                            func=self._create_tool_callable(tool.name),
                        )
                        for tool in tools_response.tools
                    ]
                    logger.info(f"Discovered tools: {[tool.name for tool in tools]}")
                    return tools
                except Exception as e:
                    logger.error(f"Error listing tools: {e}")
                    raise RuntimeError("Failed to list tools.") from e

    def _create_tool_callable(self, tool_name: str) -> Callable[..., Any]:
        """
        Dynamically create a callable function for the specified tool.

        Args:
            tool_name (str): The name of the tool.

        Returns:
            Callable: An async callable function for the tool.
        """
        async def dynamic_tool_func(**kwargs) -> Any:
            """
            Invoke the tool with the provided arguments within a session context.

            Args:
                kwargs: Arguments for the tool.

            Returns:
                Any: The result of the tool execution.
            """
            server_params = StdioServerParameters(
                command=self.command, args=self.args, env=self.env
            )
            async with stdio_client(server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    try:
                        logger.info(f"Calling tool '{tool_name}' with arguments: {kwargs}")
                        result = await session.call_tool(tool_name, kwargs)
                        logger.info(f"Tool '{tool_name}' executed successfully: {result}")
                        return result
                    except Exception as e:
                        logger.error(f"Failed to execute tool '{tool_name}': {e}")
                        raise RuntimeError(f"Tool execution failed: {e}") from e

        dynamic_tool_func.dynamic = True
        return dynamic_tool_func
