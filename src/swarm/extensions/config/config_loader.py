"""
Configuration Loader for Open Swarm MCP Framework.

This module provides functionality to:
- Load and validate server configurations from JSON files.
- Resolve environment variable placeholders.
- Ensure all required keys and configurations are present.
"""

import os
import json
import re
import logging
from typing import Any, Dict, List, Tuple, Union, Optional
from dotenv import load_dotenv

# Initialize logger for this module
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
stream_handler = logging.StreamHandler()
formatter = logging.Formatter("[%(levelname)s] %(asctime)s - %(name)s - %(message)s")
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)

# Load environment variables from .env
load_dotenv()
logger.info("Environment variables loaded from .env file.")


def resolve_placeholders(obj: Any) -> Any:
    """
    Recursively resolve placeholders in the given object.

    Placeholders are in the form of ${VAR_NAME} and are replaced with the corresponding environment variable.

    Args:
        obj (Any): The object to resolve placeholders in.

    Returns:
        Any: The object with all placeholders resolved.

    Raises:
        ValueError: If a required environment variable is not set.
    """
    if isinstance(obj, dict):
        return {k: resolve_placeholders(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [resolve_placeholders(item) for item in obj]
    elif isinstance(obj, str):
        pattern = re.compile(r'\$\{(\w+)\}')
        matches = pattern.findall(obj)
        for var in matches:
            env_value = os.getenv(var)
            if env_value is None:
                logger.error(f"Environment variable '{var}' is not set but is required.")
                raise ValueError(f"Environment variable '{var}' is not set but is required.")
            obj = obj.replace(f'${{{var}}}', env_value)
            logger.debug(f"Resolved placeholder '${{{var}}}' with value '{env_value}'")
        return obj
    else:
        return obj

def load_server_config(file_path: str = None) -> dict:
    """
    Loads the server configuration from a JSON file in the root directory and resolves placeholders.

    Args:
        file_path (str): Optional custom path to the configuration file.

    Returns:
        dict: The resolved configuration.

    Raises:
        FileNotFoundError: If the configuration file does not exist.
        ValueError: If the file contains invalid JSON or unresolved placeholders.
    """
    if file_path is None:
        file_path = os.path.join(os.getcwd(), "swarm_settings.json")
    
    logger.debug(f"Loading configuration from {file_path}")
    
    try:
        with open(file_path, "r") as file:
            config = json.load(file)
    except FileNotFoundError:
        raise FileNotFoundError(f"Configuration file not found at {file_path}")
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in configuration file {file_path}: {e}")

    logger.info(f"Configuration loaded from {file_path}: {config}")

    # Resolve placeholders recursively
    resolved_config = resolve_placeholders(config)
    logger.debug(f"Configuration after resolving placeholders: {resolved_config}")

    return resolved_config

def validate_mcp_server_env(mcp_servers: Dict[str, Any]) -> None:
    """
    Validates that mandatory environment variables in MCP server configurations are set.

    Args:
        mcp_servers (Dict[str, Any]): MCP server configurations.

    Raises:
        ValueError: If any mandatory environment variable in an `env` section is not set.
    """
    for server_name, server_config in mcp_servers.items():
        logger.debug(f"Validating environment variables for MCP server '{server_name}'.")
        env_vars = server_config.get("env", {})
        for env_key, env_value in env_vars.items():
            logger.debug(f"Checking environment variable '{env_key}' for server '{server_name}': {env_value}")
            if not env_value:
                logger.error(f"Environment variable '{env_key}' for MCP server '{server_name}' is not set.")
                raise ValueError(f"Environment variable '{env_key}' for MCP server '{server_name}' is not set.")
            logger.debug(f"Environment variable '{env_key}' is set with value: {env_value}.")


def validate_api_keys(config: Dict[str, Any], selected_llm: str = "default") -> Dict[str, Any]:
    """
    Validates the presence of API keys for the selected LLM profile.

    Args:
        config (Dict[str, Any]): The configuration dictionary.
        selected_llm (str): The selected LLM profile. Defaults to "default".

    Returns:
        Dict[str, Any]: The validated configuration.

    Raises:
        ValueError: If a required API key is missing for the selected LLM profile.
    """
    logger.debug(f"Validating API keys for LLM profile '{selected_llm}'.")
    llm_config = config.get("llm", {}).get(selected_llm, {})
    if not llm_config:
        logger.warning(f"No configuration found for LLM profile '{selected_llm}'.")
        return config

    api_key = llm_config.get("api_key")
    if api_key == "":
        # An empty string explicitly means no API key is required
        logger.info(f"LLM profile '{selected_llm}' does not require an API key (explicit empty string).")
        return config
    elif not api_key:
        # If not explicitly empty but missing, raise an error
        logger.error(f"API key is missing for LLM profile '{selected_llm}'.")
        raise ValueError(f"API key is missing for LLM profile '{selected_llm}'.")

    logger.info(f"API key validation successful for LLM profile '{selected_llm}'.")
    return config


def are_required_mcp_servers_configured(
    required_servers: List[str], config: Dict[str, Any]
) -> Tuple[bool, List[str]]:
    """
    Checks if all required MCP servers are configured.

    Args:
        required_servers (List[str]): A list of required MCP server names.
        config (Dict[str, Any]): The configuration dictionary.

    Returns:
        Tuple[bool, List[str]]: A tuple containing:
            - A boolean indicating if all required servers are present.
            - A list of missing server names.
    """
    logger.debug(f"Checking required MCP servers: {required_servers}.")
    mcp_servers = config.get("mcpServers", {})
    missing_servers = [server for server in required_servers if server not in mcp_servers]

    if missing_servers:
        logger.warning(f"Missing MCP servers: {missing_servers}.")
        return False, missing_servers

    logger.info("All required MCP servers are configured.")
    return True, []
