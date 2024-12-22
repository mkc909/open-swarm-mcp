# src/open_swarm_mcp/agent/agent_builder.py

import importlib
from typing import Dict, Any, Callable
from swarm import Agent
from open_swarm_mcp.utils.logger import setup_logger

logger = setup_logger(__name__)

async def build_agent(config: Dict[str, Any]) -> Agent:
    """
    Builds a simple Agent based on the configuration.
    
    Args:
        config (Dict[str, Any]): Configuration dictionary.
    
    Returns:
        Agent: Configured Swarm Agent.
    """
    agent_name = config.get("agentName", "EchoAgent")
    instructions = config.get("instructions", "You are a helpful agent that echoes user inputs.")
    agent = Agent(name=agent_name, instructions=instructions)
    return agent

async def build_agent_with_mcp_tools(config: Dict[str, Any]) -> Agent:
    """
    Builds an Agent with MCP tools based on the provided configuration.
    
    Args:
        config (Dict[str, Any]): Configuration dictionary containing MCP server and tool details.
    
    Returns:
        Agent: Configured Swarm Agent with registered MCP tools.
    """
    try:
        # Initialize the Agent with a name and instructions
        agent_name = config.get("agentName", "DynamicMCPAgent")
        instructions = config.get("instructions", "You are an intelligent agent with access to various tools.")
        agent = Agent(name=agent_name, instructions=instructions)
        
        # Retrieve MCP server configurations
        mcp_servers = config.get("mcpServers", {})
        
        # Iterate over each MCP server to register its tools
        for server_name, server_config in mcp_servers.items():
            tools = server_config.get("tools", [])
            for tool in tools:
                tool_name = tool.get("name")
                tool_description = tool.get("description", f"No description for {tool_name}")
                
                if not tool_name:
                    logger.warning(f"Tool without a name found in server '{server_name}'. Skipping.")
                    continue
                
                # Create the tool function dynamically
                tool_function = create_tool_function(tool_name, tool)
                
                # Register the tool with the Agent
                agent.register_tool(name=tool_name, func=tool_function, description=tool_description)
                logger.info(f"Registered tool '{tool_name}' with Agent '{agent_name}'.")
        
        logger.info("Agent built successfully with MCP tools.")
        return agent
    except Exception as e:
        logger.error(f"Failed to build agent: {e}")
        raise e

def create_tool_function(tool_name: str, tool_config: Dict[str, Any]) -> Callable[..., Any]:
    """
    Dynamically creates an asynchronous tool function based on the tool configuration.
    
    Args:
        tool_name (str): The name of the tool.
        tool_config (Dict[str, Any]): Configuration dictionary for the tool.
    
    Returns:
        Callable[..., Any]: An asynchronous function that executes the tool.
    """
    async def tool_function(**kwargs):
        """
        Executes the tool with the provided arguments.
        
        Args:
            **kwargs: Arbitrary keyword arguments for tool execution.
        
        Returns:
            Any: The result of the tool execution.
        """
        try:
            logger.info(f"Executing tool '{tool_name}' with arguments: {kwargs}")
            # Implement the actual logic to interact with the MCP server.
            # This could involve making API calls, running subprocesses, etc.
            # Example: If using HTTP requests to MCP server
            import aiohttp

            mcp_endpoint = tool_config.get("endpoint")
            if not mcp_endpoint:
                raise ValueError(f"No endpoint defined for tool '{tool_name}'.")

            async with aiohttp.ClientSession() as session:
                async with session.post(mcp_endpoint, json=kwargs) as response:
                    if response.status == 200:
                        data = await response.json()
                        logger.info(f"Tool '{tool_name}' executed successfully.")
                        return data.get("result", "No result returned.")
                    else:
                        error_msg = f"MCP server responded with status {response.status}."
                        logger.error(error_msg)
                        return error_msg

        except Exception as e:
            logger.error(f"Error executing tool '{tool_name}': {e}")
            return f"Error executing tool '{tool_name}': {e}"
    
    # Optionally, set function metadata based on tool_config
    tool_function.__name__ = tool_name
    tool_function.__doc__ = tool_config.get("description", f"No description for {tool_name}")
    
    return tool_function
