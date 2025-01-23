import asyncio
import logging
import os
from contextlib import AsyncExitStack
from typing import Any, Dict, List, Optional, Callable

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from swarm.types import Tool

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class MCPClient:
    """Manages connections and interactions with MCP servers using the MCP Python SDK."""

    def __init__(
        self,
        server_config: Dict[str, Any],
        timeout: int = 30,
    ):
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
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()

        logger.info(f"Initialized MCPClient with command={self.command} args={self.args}")

    async def initialize_session(self) -> None:
        """Initialize the MCP client session."""
        try:
            server_params = StdioServerParameters(
                command=self.command, args=self.args, env=self.env
            )
            stdio_transport = await self.exit_stack.enter_async_context(
                stdio_client(server_params)
            )
            read, write = stdio_transport
            self.session = await self.exit_stack.enter_async_context(
                ClientSession(read, write)
            )
            await self.session.initialize()
            logger.info("MCPClient session initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize MCP client session: {e}")
            await self.cleanup()
            raise RuntimeError("Initialization failed.") from e

    async def list_tools(self) -> List[Tool]:
        """Discover tools from the MCP server."""
        if not self.session:
            await self.initialize_session()

        tools_response = await self.session.list_tools()
        tools = [
            Tool(
                name=tool.name,
                description=tool.description,
                input_schema=tool.inputSchema,
                func=await self._create_tool_callable(tool.name),
            )
            for tool in tools_response.tools
        ]
        logger.info(f"Discovered tools: {[tool.name for tool in tools]}")
        return tools

    async def _create_tool_callable(self, tool_name: str) -> Callable[..., Any]:
        """Dynamically create a callable function for the specified tool."""
        async def dynamic_tool_func(**kwargs) -> Any:
            """Invoke the tool with the provided arguments."""
            if not self.session:
                await self.initialize_session()

            logger.info(f"Calling tool '{tool_name}' with arguments: {kwargs}")
            try:
                result = await self.session.call_tool(tool_name, kwargs)
                logger.info(f"Tool '{tool_name}' executed successfully: {result}")
                return result
            except Exception as e:
                logger.error(f"Failed to execute tool '{tool_name}': {e}")
                raise RuntimeError(f"Tool execution failed: {e}") from e

        # Mark the function as dynamic for Swarm compatibility
        dynamic_tool_func.dynamic = True
        return dynamic_tool_func

    async def execute_tool(self, tool: Tool, arguments: Dict[str, Any]) -> Any:
        """
        Convenience method to execute a tool.

        Args:
            tool: The tool to execute.
            arguments: The arguments to pass to the tool.

        Returns:
            The result of tool execution.
        """
        logger.debug(f"Executing tool '{tool.name}' with arguments: {arguments}")
        return await tool.func(**arguments)

    async def cleanup(self) -> None:
        """Clean up resources and terminate the session."""
        try:
            await self.exit_stack.aclose()
            self.session = None
            logger.info("MCPClient resources cleaned up successfully.")
        except Exception as e:
            logger.error(f"Error during MCPClient cleanup: {e}")
