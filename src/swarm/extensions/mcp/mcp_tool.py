from typing import Any, Dict, List
from src.swarm.extensions.mcp.mcp_client import MCPClient
from src.swarm.types import Tool
from .mcp_tool import MCPTool
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

class MCPToolProvider:
    """
    Provides tools available from an MCP server.
    """

    def __init__(self, mcp_client: MCPClient):
        """
        Initialize the MCPToolProvider.

        :param mcp_client: An instance of MCPClient.
        """
        self.mcp_client = mcp_client
        self._cached_tools = None  # Cache for discovered tools
        logger.debug("Initialized MCPToolProvider with MCPClient.")

    def discover_tools(self, refresh: bool = False) -> List[Tool]:
        """
        Discover tools available on the connected MCP server.

        :param refresh: If True, refresh the tool list even if cached.
        :return: A list of MCPTool objects.
        """
        if self._cached_tools and not refresh:
            logger.debug("Returning cached tools.")
            return self._cached_tools

        try:
            logger.info("Discovering tools from the MCP server...")
            tools = self.mcp_client.list_tools()
            self._cached_tools = [
                MCPTool(
                    name=tool.name,
                    description=tool.description,
                    input_schema=tool.input_schema,
                    mcp_provider=self,
                )
                for tool in tools
            ]
            logger.debug(f"Discovered tools: {[tool.name for tool in self._cached_tools]}")
            return self._cached_tools
        except Exception as e:
            logger.error(f"Error discovering tools: {str(e)}", exc_info=True)
            raise RuntimeError(f"Error discovering tools: {str(e)}")

    def call_method(self, method_name: str, input_data: Dict[str, Any]) -> Any:
        """
        Call a specific tool method on the MCP server.

        :param method_name: Name of the tool method.
        :param input_data: Input data for the method.
        :return: Response from the MCP server.
        """
        logger.debug(f"Calling method '{method_name}' with input: {input_data}")
        try:
            response = self.mcp_client.call_tool(method_name, input_data)
            logger.debug(f"Response from method '{method_name}': {response}")
            return response
        except Exception as e:
            logger.error(f"Error calling method '{method_name}': {str(e)}", exc_info=True)
            raise RuntimeError(f"Error calling method '{method_name}': {str(e)}")
