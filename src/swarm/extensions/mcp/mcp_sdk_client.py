"""
MCP Client using the official MCP Python SDK
------------------------------------------
This module provides a client implementation using the official MCP Python SDK
for better compatibility and maintainability.
"""

import logging
from typing import List, Dict, Any, Optional, Callable
from mcp import Client, Tool as MCPTool
from swarm.settings import DEBUG
from swarm.types import Tool

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG if DEBUG else logging.INFO)


class MCPSDKClient:
    """
    MCPSDKClient manages communication with MCP servers using the official SDK.
    """

    def __init__(
        self,
        command: str,
        args: Optional[List[str]] = None,
        env: Optional[Dict[str, str]] = None,
        timeout: int = 30,
    ):
        """
        Initialize the MCP SDK client.

        Args:
            command (str): Command to start the MCP server
            args (List[str], optional): Command arguments
            env (Dict[str, str], optional): Environment variables
            timeout (int): Operation timeout in seconds
        """
        self.command = command
        self.args = args or []
        self.env = env or {}
        self.timeout = timeout
        self._client: Optional[Client] = None
        self._tools_cache: Optional[Dict[str, Tool]] = None
        
        logger.debug(
            f"Initialized MCPSDKClient with command='{command}', args={args}, timeout={timeout}"
        )

    async def _ensure_client(self) -> Client:
        """
        Ensure we have an active client connection.
        
        Returns:
            Client: The MCP client instance
        """
        if not self._client:
            try:
                self._client = Client(
                    command=self.command,
                    args=self.args,
                    env=self.env,
                    timeout=self.timeout
                )
                await self._client.initialize()
                logger.debug("Successfully created new MCP client connection")
            except Exception as e:
                logger.error(f"Failed to create MCP client: {e}")
                raise
        return self._client

    async def discover_tools(self) -> List[Tool]:
        """
        Discover available tools from the MCP server.
        
        Returns:
            List[Tool]: List of discovered tools
        """
        try:
            client = await self._ensure_client()
            mcp_tools = await client.list_tools()
            
            tools = []
            for mcp_tool in mcp_tools:
                tool_func = await self._create_tool_callable(mcp_tool.name)
                tool = Tool(
                    name=mcp_tool.name,
                    description=mcp_tool.description or "No description provided.",
                    func=tool_func,
                    input_schema=mcp_tool.input_schema,
                )
                tools.append(tool)
                
            # Update cache
            self._tools_cache = {tool.name: tool for tool in tools}
            
            logger.debug(f"Discovered tools: {[tool.name for tool in tools]}")
            return tools
            
        except Exception as e:
            logger.error(f"Tool discovery failed: {e}")
            raise

    async def _create_tool_callable(self, tool_name: str) -> Callable[..., Any]:
        """
        Create a callable function for a specific tool.
        
        Args:
            tool_name (str): Name of the tool
            
        Returns:
            Callable: Async function that executes the tool
        """
        async def tool_func(**kwargs) -> Any:
            try:
                client = await self._ensure_client()
                result = await client.call_tool(tool_name, kwargs)
                
                if result.is_error:
                    logger.error(f"Tool '{tool_name}' returned error: {result.error}")
                    raise RuntimeError(f"Tool '{tool_name}' error: {result.error}")
                
                # Process result content
                if result.content:
                    content = result.content[0]
                    if content.type == "text":
                        return content.text.strip()
                    elif content.type == "json":
                        return content.json
                    else:
                        logger.warning(f"Unexpected content type: {content.type}")
                        return content.text
                        
                return None
                
            except Exception as e:
                logger.error(f"Error executing tool '{tool_name}': {e}")
                raise
                
        # Mark as dynamic tool
        tool_func.dynamic = True
        return tool_func

    async def get_tools(self, agent_name: str) -> List[Tool]:
        """
        Get tools, using cache if available.
        
        Args:
            agent_name (str): Name of the agent requesting tools
            
        Returns:
            List[Tool]: List of available tools
        """
        if self._tools_cache is not None:
            logger.debug(f"Returning cached tools for agent '{agent_name}'")
            return list(self._tools_cache.values())
            
        logger.debug(f"No cached tools found for agent '{agent_name}'. Discovering tools...")
        return await self.discover_tools()

    async def call_tool(self, tool: Tool, arguments: Dict[str, Any]) -> Any:
        """
        Call a specific tool.
        
        Args:
            tool (Tool): Tool to call
            arguments (Dict[str, Any]): Tool arguments
            
        Returns:
            Any: Tool execution result
        """
        logger.debug(f"Calling tool '{tool.name}' with arguments: {arguments}")
        return await tool.func(**arguments)

    async def close(self):
        """
        Close the client connection.
        """
        if self._client:
            await self._client.close()
            self._client = None
            self._tools_cache = None
            logger.debug("Closed MCP client connection")
