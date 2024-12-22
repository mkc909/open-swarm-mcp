# src/open_swarm_mcp/config/config_loader.py

import json
import os
import logging
from typing import Any, Dict, Tuple, List

from open_swarm_mcp.utils.logger import setup_logger

logger = setup_logger(__name__)

# Mapping of LLM providers to their respective API key environment variables
LLM_PROVIDER_API_KEY_MAP = {
    "openai": "OPENAI_API_KEY",
    "ollama": "OLLAMA_API_KEY",
    # Add other providers and their API key environment variables here
}

def load_server_config(config_path: str) -> Dict[str, Any]:
    """
    Load the MCP server configuration from a JSON file.

    Args:
        config_path (str): Path to the configuration file.

    Returns:
        Dict[str, Any]: Configuration dictionary.

    Raises:
        FileNotFoundError: If the configuration file does not exist.
        json.JSONDecodeError: If the configuration file is not valid JSON.
    """
    logger.debug(f"Attempting to load server configuration from '{config_path}'")
    if not os.path.exists(config_path):
        logger.error(f"Configuration file not found at {config_path}.")
        raise FileNotFoundError(f"Configuration file not found at {config_path}.")

    with open(config_path, 'r') as f:
        config = json.load(f)

    logger.info(f"Configuration loaded from {config_path}.")
    logger.debug(f"Loaded configuration: {config}")
    return config

def validate_api_keys(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate that all required API keys are present in environment variables.

    Args:
        config (Dict[str, Any]): Configuration dictionary.

    Returns:
        Dict[str, Any]: Updated configuration dictionary with API keys injected from environment variables.

    Raises:
        ValueError: If any required API key is missing.
    """
    logger.debug("Validating API keys in configuration")
    llm_config = config.get('llm', {})
    llm_provider = llm_config.get('provider', 'openai')
    expected_api_key_env_var = LLM_PROVIDER_API_KEY_MAP.get(llm_provider, "LLM_API_KEY")

    llm_api_key = os.getenv(expected_api_key_env_var)
    if not llm_api_key:
        logger.error(f"LLM API Key is missing for provider '{llm_provider}'. Please set the '{expected_api_key_env_var}' environment variable.")
        raise ValueError(f"LLM API Key is missing. Please set the '{expected_api_key_env_var}' environment variable in your .env file.")
    config['llm']['api_key'] = llm_api_key
    logger.info(f"LLM API Key loaded from environment variable '{expected_api_key_env_var}'.")

    # Validate MCP server API keys
    mcp_servers = config.get('mcpServers', {})
    for server, details in mcp_servers.items():
        env_vars = details.get('env', {})
        for env_var, value in env_vars.items():
            if not value:
                env_value = os.getenv(env_var)
                if not env_value:
                    logger.error(f"Environment variable '{env_var}' for server '{server}' is missing.")
                    raise ValueError(f"Environment variable '{env_var}' for server '{server}' is missing. Please set it in the .env file.")
                config['mcpServers'][server]['env'][env_var] = env_value
                logger.info(f"Environment variable '{env_var}' for server '{server}' loaded from environment variables.")

    logger.info("All required API keys are present.")
    return config

def are_required_mcp_servers_running(required_servers: List[str], config: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Check if all required MCP servers are configured.

    Args:
        required_servers (List[str]): List of required MCP server names.
        config (Dict[str, Any]): Configuration dictionary.

    Returns:
        Tuple[bool, List[str]]: A tuple containing a boolean indicating if all servers are configured,
                                and a list of missing servers.
    """
    logger.debug(f"Checking if required MCP servers are running: {required_servers}")
    mcp_servers = config.get('mcpServers', {})
    missing_servers = [server for server in required_servers if server not in mcp_servers or not mcp_servers[server]]

    if missing_servers:
        logger.warning(f"Missing MCP servers: {', '.join(missing_servers)}")
        return False, missing_servers
    else:
        logger.info("All required MCP servers are configured.")
        return True, []
