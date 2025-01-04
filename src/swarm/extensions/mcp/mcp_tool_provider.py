import logging
from typing import Callable, Dict, List, Any, Optional
from swarm.types import Agent, Tool
from .mcp_client import MCPClientManager

logger = logging.getLogger(__name__)

class MCPToolProvider:
    """
    High-level abstraction for dynamically discovering and integrating tools from an MCP server.
    This class interacts with an MCPClientManager to fetch tool definitions and provides callable functions
    for each tool with appropriate metadata and input validation.
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

    def initialize_client(self):
        # Initialize the MCP client
        self.client = MCPClientManager(
            command=self.config.get("command", "npx"),
            args=self.config.get("args", []),
            env=self.config.get("env", {}),
            timeout=self.config.get("timeout", 30),
        )

    async def discover_tools(self, agent: Agent) -> list[Tool]:
        """
        Discover tools for the given agent using the associated MCP server.
        
        Args:
            agent (Agent): The agent for which to discover tools.

        Returns:
            list[Tool]: A list of discovered tools.
        """
        try:
            logger.debug(f"Starting tool discovery for agent '{agent.name}' on MCP server '{self.server_name}'.")

            # Call the correct method on the MCP client
            raw_responses = await self.client.initialize_and_list_tools()

            logger.debug(f"Raw responses from MCP server '{self.server_name}': {raw_responses}")

            tools_data = [
                tool for response in raw_responses
                if "result" in response and "tools" in response["result"]
                for tool in response["result"]["tools"]
            ]

            discovered_tools = [
                Tool(
                    name=tool_info["name"],
                    description=tool_info.get("description", "No description provided."),
                    func=self.client._create_tool_callable(tool_info["name"]),
                    input_schema=tool_info.get("inputSchema", {}),
                )
                for tool_info in tools_data
            ]

        finally:
            logger.info(f"Discovered tools for agent '{agent.name}': {[tool.name for tool in discovered_tools]}")
            return discovered_tools

    def _create_tool_function(self, tool_info: Dict[str, Any]) -> Callable:
        """
        Create a callable function for a specific tool based on its metadata.

        Args:
            tool_info (Dict[str, Any]): Metadata for the tool.

        Returns:
            Callable: A Python function representing the tool.
        """
        tool_name = tool_info.get("name")
        tool_description = tool_info.get("description", "No description available.")
        tool_input_schema = tool_info.get("inputSchema", {})

        if not tool_name:
            raise ValueError("Tool metadata must include a 'name'.")

        logger.debug(f"Creating callable function for tool '{tool_name}' with schema: {tool_input_schema}")

        def tool_function(**kwargs):
            """
            Callable representation of the MCP tool.

            Args:
                **kwargs: Parameters required by the tool.

            Returns:
                Any: The result from the MCP server.
            """
            logger.debug(f"Invoking tool '{tool_name}' with arguments: {kwargs}")

            # Validate input parameters against the schema
            self._validate_input(tool_name, tool_input_schema, kwargs)

            # Execute the tool via MCPClientManager
            try:
                result = self.client.execute_tool(tool_name, params=kwargs)
                logger.debug(f"Tool '{tool_name}' executed successfully. Result: {result}")
                return result
            except Exception as e:
                logger.error(f"Error executing tool '{tool_name}': {e}")
                raise

        # Add metadata to the function for documentation
        tool_function.__name__ = tool_name
        tool_function.__doc__ = tool_description

        logger.debug(f"Callable function for tool '{tool_name}' created successfully.")
        return tool_function

    def _validate_input(self, tool_name: str, schema: Dict[str, Any], params: Dict[str, Any]):
        """
        Validate input parameters against the tool's schema.

        Args:
            tool_name (str): The name of the tool being validated.
            schema (Dict[str, Any]): The JSON schema of the tool's input.
            params (Dict[str, Any]): The input parameters to validate.

        Raises:
            ValueError: If validation fails.
        """
        logger.debug(f"Validating input for tool '{tool_name}' with schema: {schema} and params: {params}")

        required_fields = schema.get("required", [])
        for field in required_fields:
            if field not in params:
                raise ValueError(f"Missing required field '{field}' for tool '{tool_name}'.")

        additional_properties = schema.get("additionalProperties", True)
        if not additional_properties:
            valid_fields = set(schema.get("properties", {}).keys())
            invalid_fields = [key for key in params if key not in valid_fields]
            if invalid_fields:
                raise ValueError(
                    f"Invalid fields for tool '{tool_name}': {invalid_fields}. Allowed fields: {valid_fields}"
                )

        logger.debug(f"Input for tool '{tool_name}' validated successfully.")

    def get_tool(self, tool_name: str) -> Optional[Callable]:
        """
        Retrieve a callable tool function by name.

        Args:
            tool_name (str): The name of the tool.

        Returns:
            Callable: The callable function for the tool, or None if not found.
        """
        tool = self.tools.get(tool_name)
        if tool:
            logger.debug(f"Retrieved tool '{tool_name}' from MCPToolProvider.")
        else:
            logger.warning(f"Tool '{tool_name}' not found in MCPToolProvider.")
        return tool

    def list_tools(self) -> List[str]:
        """
        List the names of all registered tools.

        Returns:
            List[str]: A list of tool names.
        """
        tool_names = list(self.tools.keys())
        logger.debug(f"Listing tools from MCPToolProvider: {tool_names}")
        return tool_names
