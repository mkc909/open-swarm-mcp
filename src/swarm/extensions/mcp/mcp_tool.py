from src.swarm.types import Tool

class MCPTool(Tool):
    def __init__(
        self,
        name: str,
        description: str,
        input_schema: Dict[str, Any],
        mcp_provider: Any,
    ):
        """
        Initialize an MCPTool object.

        :param name: Name of the tool.
        :param description: Description of the tool.
        :param input_schema: Schema defining the tool's inputs.
        :param mcp_provider: The MCP provider responsible for routing requests.
        """
        super().__init__(name, func=None, description=description, input_schema=input_schema, dynamic=True)
        self.mcp_provider = mcp_provider

    def __call__(self, input_data: Dict[str, Any]):
        """
        Make the MCPTool instance callable by routing to the MCP server.
        """
        if not isinstance(input_data, dict):
            raise ValueError("Input data must be a dictionary matching the tool's input schema.")
        
        # Route the call to the MCP server using the mcp_provider
        try:
            response = self.mcp_provider.call_method(self.name, input_data)
            return response
        except Exception as e:
            raise RuntimeError(f"Error executing MCPTool '{self.name}': {str(e)}")
