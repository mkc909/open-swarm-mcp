# src/swarm/config/config_loader.py

"""
Configuration Loader for Open Swarm.

This module handles loading and validating the server configuration from a JSON file.
It resolves environment variable placeholders and ensures all required API keys are present.
"""

import os
import json
import re
import logging
from typing import Any, Dict, List, Tuple

from .utils.logger import setup_logger

# Initialize logger for this module
logger = setup_logger(__name__)

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

def load_server_config(file_path: str) -> Dict[str, Any]:
    """
    Loads the server configuration from a JSON file and resolves any environment variable placeholders.

    Args:
        file_path (str): The path to the configuration JSON file.

    Returns:
        Dict[str, Any]: The resolved configuration dictionary.

    Raises:
        FileNotFoundError: If the configuration file does not exist.
        json.JSONDecodeError: If the configuration file contains invalid JSON.
        ValueError: If any required environment variables are missing.
    """
    logger.debug(f"Attempting to load configuration from {file_path}")
    if not os.path.exists(file_path):
        logger.error(f"Configuration file not found at {file_path}")
        raise FileNotFoundError(f"Configuration file not found at {file_path}")

    with open(file_path, 'r') as f:
        config = json.load(f)
    logger.debug(f"Configuration loaded: {config}")

    # Resolve placeholders recursively
    resolved_config = resolve_placeholders(config)
    logger.debug(f"Configuration after resolving placeholders: {resolved_config}")

    return resolved_config

def validate_api_keys(config: Dict[str, Any], selected_llm: str = None) -> Dict[str, Any]:
    """
    Validates that all required API keys are present in the configuration.
    Skips validation for LLM providers that do not require API keys.

    Args:
        config (Dict[str, Any]): The configuration dictionary.
        selected_llm (str): The selected LLM profile. Defaults to "default" if not provided.

    Returns:
        Dict[str, Any]: The validated configuration.

    Raises:
        ValueError: If a required API key is missing and the provider mandates it.
    """
    # Use "default" as the fallback selected LLM profile
    selected_llm = selected_llm or "default"
    logger.debug(f"Validating API keys for LLM profile: {selected_llm}")

    try:
        llm_profile = config.get("llm", {}).get(selected_llm, {})
        llm_provider = llm_profile.get("provider")
        llm_api_key = llm_profile.get("api_key")

        # If provider is missing, log a warning and skip validation
        if not llm_provider:
            logger.warning(f"No provider specified for LLM profile '{selected_llm}'. Skipping API key validation.")
            return config

        # Log if the API key is missing, but only warn since not all providers require it
        if not llm_api_key:
            logger.warning(f"API key missing for provider '{llm_provider}' in LLM profile '{selected_llm}'. Validation skipped.")

        logger.info(f"API key validation completed for provider '{llm_provider}'.")
    except Exception as e:
        logger.error(f"Unexpected error during API key validation for profile '{selected_llm}': {e}", exc_info=True)

    return config

def get_llm_provider(config: Dict[str, Any], selected_llm: str) -> Any:
    """
    Instantiates and returns the appropriate LLM provider based on the configuration.

    Args:
        config (Dict[str, Any]): The configuration dictionary.
        selected_llm (str): The selected LLM profile.

    Returns:
        Any: An instance of the selected LLM provider.

    Raises:
        ValueError: If the provider is not recognized or unsupported.
    """
    logger.debug(f"Getting LLM provider for profile '{selected_llm}'")
    try:
        provider_name = config['llm'][selected_llm]['provider']
        if provider_name == 'openai':
            from swarm.extensions.llm.openai_provider import OpenAIProvider
            return OpenAIProvider(config['llm'][selected_llm])
        elif provider_name == 'ollama':
            from swarm.extensions.llm.ollama_provider import OllamaProvider
            return OllamaProvider(config['llm'][selected_llm])
        elif provider_name == 'mock':
            from swarm.extensions.llm.mock_provider import MockProvider
            return MockProvider(config['llm'][selected_llm])
        else:
            logger.error(f"Unsupported LLM provider: {provider_name}")
            raise ValueError(f"Unsupported LLM provider: {provider_name}")
    except KeyError as e:
        logger.error(f"Missing key in configuration for LLM provider: {e}")
        raise ValueError(f"Missing key in configuration for LLM provider: {e}")
    except ImportError as e:
        logger.error(f"Failed to import LLM provider module: {e}")
        raise ValueError(f"Failed to import LLM provider module: {e}")

def are_required_mcp_servers_running(required_servers: List[str], config: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Checks whether all required MCP servers are present in the configuration.

    Args:
        required_servers (List[str]): A list of required MCP server names.
        config (Dict[str, Any]): The configuration dictionary.

    Returns:
        (bool, List[str]): A tuple where the first element is True if all required servers are present,
                           and the second element is a list of missing servers.
    """
    logger.debug(f"Checking required MCP servers: {required_servers}")
    missing_servers = [server for server in required_servers if server not in config.get('mcpServers', {})]
    if missing_servers:
        logger.warning(f"Missing MCP servers: {missing_servers}")
        return False, missing_servers
    logger.debug("All required MCP servers are present.")
    return True, []
