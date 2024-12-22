# src/open_swarm_mcp/agent/agent_builder.py

import requests
from typing import Dict, Any, Callable, List
from swarm import Agent
from open_swarm_mcp.utils.logger import setup_logger

logger = setup_logger(__name__)

def build_agent(config: Dict[str, Any]) -> Agent:
    """
    Builds a simple Agent based on the configuration.
    
    Args:
        config (Dict[str, Any]): Configuration dictionary.
    
    Returns:
        Agent: Configured Swarm Agent.
    """
    agent_name = config.get("agentName", "EchoAgent")
    instructions = config.get("instructions", "You are a helpful agent that echoes user inputs.")
    
    # Initialize the Agent with a name and instructions
    agent = Agent(
        name=agent_name,
        instructions=instructions,
        functions=[]  # No tools registered
    )
    
    logger.info(f"Built simple Agent '{agent_name}' without tools.")
    return agent

def build_agent_with_mcp_tools(config: Dict[str, Any]) -> Agent:
    """
    Builds an Agent with MCP tools based on the provided configuration.
    
    Args:
        config (Dict[str, Any]): Configuration dictionary containing MCP server and tool details.
    
    Returns:
        Agent: Configured Swarm Agent with registered MCP tools.
    """
    try:
        # Initialize Agent parameters
        agent_name = config.get("agentName", "DynamicMCPAgent")
        instructions = config.get("instructions", "You are an intelligent agent with access to various tools.")
        
        # Retrieve MCP server configurations
        mcp_servers = config.get("mcpServers", {})
        
        # Collect all tool functions
        tool_functions: List[Callable[..., Any]] = []
        
        for server_name, server_config in mcp_servers.items():
            tools = server_config.get("tools", [])
            for tool in tools:
                tool_name = tool.get("name")
                tool_description = tool.get("description", f"No description for '{tool_name}'")
                mcp_endpoint = tool.get("endpoint")
                
                if not tool_name:
                    logger.warning(f"Tool without a name found in server '{server_name}'. Skipping.")
                    continue
                if not mcp_endpoint:
                    logger.warning(f"Tool '{tool_name}' in server '{server_name}' lacks an endpoint. Skipping.")
                    continue
                
                # Create the tool function
                tool_function = create_tool_function(tool_name, tool_description, mcp_endpoint)
                
                tool_functions.append(tool_function)
                logger.info(f"Registered tool '{tool_name}' for MCP server '{server_name}'.")
        
        # Initialize the Agent with the collected tool functions
        agent = Agent(
            name=agent_name,
            instructions=instructions,
            functions=tool_functions  # Pass tools directly here
        )
        
        logger.info(f"Agent '{agent_name}' built successfully with {len(tool_functions)} MCP tools.")
        return agent
    except Exception as e:
        logger.error(f"Failed to build Agent with MCP tools: {e}")
        raise e

def create_tool_function(tool_name: str, tool_description: str, mcp_endpoint: str) -> Callable[..., Any]:
    """
    Creates a synchronous tool function that proxies requests to an MCP server.
    
    Args:
        tool_name (str): The name of the tool.
        tool_description (str): Description of the tool.
        mcp_endpoint (str): The MCP server endpoint for the tool.
    
    Returns:
        Callable[..., Any]: A synchronous function that executes the tool.
    """
    def tool_function(**kwargs) -> Any:
        """
        Executes the tool by sending a request to the MCP server.
        
        Args:
            **kwargs: Arbitrary keyword arguments for tool execution.
        
        Returns:
            Any: The result from the MCP server or an error message.
        """
        try:
            logger.info(f"Executing tool '{tool_name}' with arguments: {kwargs}")
            
            # Send a POST request to the MCP server endpoint with the provided arguments
            response = requests.post(mcp_endpoint, json=kwargs, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                result = data.get("result", "No result returned from MCP server.")
                logger.info(f"Tool '{tool_name}' executed successfully. Result: {result}")
                return result
            else:
                error_msg = f"MCP server responded with status {response.status_code}: {response.text}"
                logger.error(error_msg)
                return error_msg
        except requests.exceptions.RequestException as e:
            error_msg = f"HTTP request failed for tool '{tool_name}': {e}"
            logger.error(error_msg)
            return error_msg
        except ValueError as e:
            error_msg = f"Invalid JSON response from MCP server for tool '{tool_name}': {e}"
            logger.error(error_msg)
            return error_msg
        except Exception as e:
            error_msg = f"Unexpected error during execution of tool '{tool_name}': {e}"
            logger.error(error_msg)
            return error_msg
    
    # Optionally, set function metadata based on tool_description
    tool_function.__name__ = tool_name
    tool_function.__doc__ = tool_description
    
    return tool_function
