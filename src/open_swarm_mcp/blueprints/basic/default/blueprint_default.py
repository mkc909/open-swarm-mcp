# src/open_swarm_mcp/blueprints/basic/default/blueprint_default.py

from typing import Dict, Any
from open_swarm_mcp.agent.agent_builder import build_agent
from open_swarm_mcp.utils.logger import setup_logger

logger = setup_logger(__name__)

# Define EXAMPLE_METADATA for the default blueprint
EXAMPLE_METADATA = {
    "title": "Default Simple Agent",
    "description": "A simple agent that echoes user inputs.",
    "required_mcp_servers": [],
    "env_vars": []
}

async def initialize_agent(config: Dict[str, Any]):
    """
    Initializes a simple Agent that echoes user inputs.
    
    Args:
        config (Dict[str, Any]): Configuration dictionary.
    
    Returns:
        Agent: Configured agent.
    """
    from swarm import Agent

    agent = await build_agent(config)
    # Optionally, register any default tools here if needed
    return agent
