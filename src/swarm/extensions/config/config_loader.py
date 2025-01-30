# src/swarm/extensions/config/config_loader.py

"""
Configuration Loader for Open Swarm MCP Framework.

This module provides functionality to:
- Load and validate server configurations from JSON files.
- Resolve environment variable placeholders.
- Ensure all required keys and configurations are present.

Enhanced to redact sensitive information during logging and provide robust error handling.
"""

import os
import json
import re
import logging
from typing import Any, Dict, List, Tuple, Optional
from dotenv import load_dotenv
from .server_config import save_server_config
from swarm.settings import DEBUG
from swarm.utils.redact import redact_sensitive_data

# Initialize logger for this module
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG if DEBUG else logging.INFO)
stream_handler = logging.StreamHandler()
formatter = logging.Formatter("[%(levelname)s] %(asctime)s - %(name)s - %(message)s")
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)

# Load environment variables from .env
load_dotenv()
logger.debug("Environment variables loaded from .env file.")

def resolve_placeholders(obj: Any) -> Any:
    """
    Recursively resolve placeholders in the given object.

    Placeholders are in the form of ${VAR_NAME} and are replaced with the corresponding environment variable.

    Args:
        obj (Any): The object to resolve placeholders in.

    Returns:
        Any: The object with all placeholders resolved.

    Raises:
        None
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
                logger.warning(f"Environment variable '{var}' is not set but is referenced in the configuration. Placeholder will be left unresolved.")
                # Do not replace the placeholder if the env variable is not set
                continue
            logger.debug(f"Resolved placeholder '${{{var}}}' with value '{redact_sensitive_data(env_value)}'")
            obj = obj.replace(f'${{{var}}}', env_value)
        return obj
    else:
        return obj

def load_server_config(file_path: str = None) -> dict:
    """
    Loads the server configuration from a JSON file and resolves placeholders.

    Args:
        file_path (str): Optional custom path to the configuration file.

    Returns:
        dict: The resolved configuration.

    Raises:
        FileNotFoundError: If the configuration file does not exist.
        ValueError: If the file contains invalid JSON or unresolved placeholders.
    """
    if file_path is None:
        file_path = os.path.join(os.getcwd(), "swarm_config.json")

    logger.debug(f"Attempting to load configuration from {file_path}")

    try:
        with open(file_path, "r") as file:
            config = json.load(file)
            logger.debug(f"Raw configuration loaded: {redact_sensitive_data(config)}")
    except FileNotFoundError:
        logger.error(f"Configuration file not found at {file_path}")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in configuration file {file_path}: {e}")
        raise ValueError(f"Invalid JSON in configuration file {file_path}: {e}")

    # Resolve placeholders recursively
    try:
        resolved_config = resolve_placeholders(config)
        logger.debug(f"Configuration after resolving placeholders: {redact_sensitive_data(resolved_config)}")
    except Exception as e:
        logger.error(f"Failed to resolve placeholders in configuration: {e}")
        raise

    return resolved_config

def validate_mcp_server_env(mcp_servers: Dict[str, Any]) -> None:
    """
    Validates that mandatory environment variables in MCP server configurations are set.

    Args:
        mcp_servers (Dict[str, Any]): MCP server configurations.

    Raises:
        ValueError: If any mandatory environment variable in an `env` section is not set.
    """
    logger.debug(f"Validating environment variables for MCP servers: {list(mcp_servers.keys())}")
    for server_name, server_config in mcp_servers.items():
        logger.debug(f"Validating environment variables for MCP server '{server_name}'.")
        env_vars = server_config.get("env", {})
        for env_key, env_value in env_vars.items():
            logger.debug(f"Checking environment variable '{env_key}' for server '{server_name}' with value '{redact_sensitive_data(env_value)}'")
            if env_value == "":
                logger.debug(f"Environment variable '{env_key}' for MCP server '{server_name}' is optional and set to empty string.")
                # Optional: Do not raise error if env_value is empty string
                continue
            elif not env_value:
                logger.error(f"Environment variable '{env_key}' for MCP server '{server_name}' is not set.")
                raise ValueError(f"Environment variable '{env_key}' for MCP server '{server_name}' is not set.")
            else:
                logger.debug(f"Environment variable '{env_key}' for server '{server_name}' is set.")

def get_default_llm_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Retrieves the LLM configuration based on the `LLM` environment variable.

    Args:
        config (Dict[str, Any]): The configuration dictionary.

    Returns:
        Dict[str, Any]: The selected LLM configuration.

    Raises:
        ValueError: If the `LLM` environment variable is not set or the selected LLM profile is not found.
    """
    selected_llm = os.getenv("LLM", "default")
    logger.debug(f"Selected LLM profile from environment variable: '{selected_llm}'")

    llm_config = config.get("llm", {}).get(selected_llm)
    if not llm_config:
        logger.error(f"LLM profile '{selected_llm}' not found in configuration.")
        raise ValueError(f"LLM profile '{selected_llm}' not found in configuration.")

    logger.debug(f"Using LLM profile: '{selected_llm}'")
    return llm_config

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
        logger.debug(f"LLM profile '{selected_llm}' does not require an API key (explicit empty string).")
        # Optional: API key is optional if set to empty string
        return config
    elif not api_key:
        logger.error(f"API key is missing for LLM profile '{selected_llm}'.")
        raise ValueError(f"API key is missing for LLM profile '{selected_llm}'.")

    logger.debug(f"API key validation successful for LLM profile '{selected_llm}'. Key: {redact_sensitive_data(api_key)}")
    return config

def are_required_mcp_servers_configured(required_servers: List[str], config: dict) -> Tuple[bool, List[str]]:
    """
    Checks if all required MCP servers are configured in the given configuration.

    Args:
        required_servers (List[str]): List of required MCP server names.
        config (dict): Configuration dictionary.

    Returns:
        Tuple[bool, List[str]]: A tuple where the first element is True if all servers are configured,
                                 and the second element is a list of missing servers.
    """
    configured_servers = config.get("mcpServers", {}).keys()
    missing_servers = [server for server in required_servers if server not in configured_servers]
    if missing_servers:
        logger.error(f"Missing MCP servers in configuration: {missing_servers}")
        return False, missing_servers
    return True, []

def validate_and_select_llm_provider(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validates the selected LLM provider and returns its configuration.

    Args:
        config (Dict[str, Any]): The configuration dictionary.

    Returns:
        Dict[str, Any]: The validated LLM provider configuration.

    Raises:
        ValueError: If validation fails.
    """
    logger.debug("Validating and selecting LLM provider.")
    try:
        selected_llm = get_default_llm_config(config)
        validate_api_keys(config, selected_llm)
        return selected_llm
    except ValueError as e:
        logger.error(f"LLM provider validation failed: {e}")
        raise

def inject_env_vars(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Injects environment variables into the configuration where placeholders exist.

    Args:
        config (Dict[str, Any]): The configuration dictionary.

    Returns:
        Dict[str, Any]: The configuration with environment variables injected.
    """
    logger.debug("Injecting environment variables into configuration.")
    # This function is already handled by resolve_placeholders in load_server_config
    # If additional environment variable injection is needed, implement here.
    # For now, we'll assume placeholders are resolved during load.
    return config

def load_llm_config(config: Dict[str, Any], llm_name: Optional[str] = None) -> Dict[str, Any]:
    """
    Load the configuration for a specific LLM.

    Args:
        config (Dict[str, Any]): The full configuration dictionary.
        llm_name (Optional[str]): The name of the LLM to load. Defaults to None.

    Returns:
        Dict[str, Any]: The configuration dictionary for the specified LLM.

    Raises:
        ValueError: If the LLM configuration cannot be found or is invalid.
    """
    logger.debug(f"Attempting to load LLM configuration for: {llm_name or 'unspecified'}")

    # Determine LLM name
    if not llm_name:
        llm_name = os.getenv("DEFAULT_LLM", "default")
        logger.debug(f"No LLM name provided, using DEFAULT_LLM env variable or fallback to 'default': {llm_name}")

    # Load the specific LLM configuration
    llm_config = config.get("llm", {}).get(llm_name)
    if not llm_config:
        error_message = f"LLM configuration for '{llm_name}' not found in the config."
        logger.error(error_message)
        raise ValueError(error_message)

    logger.debug(f"Loaded LLM configuration for '{llm_name}': {redact_sensitive_data(llm_config)}")
    return llm_config

def get_llm_model(config: Dict[str, Any], llm_name: Optional[str] = None) -> str:
    """
    Retrieves the model name for a specific LLM.

    Args:
        config (Dict[str, Any]): The full configuration dictionary.
        llm_name (Optional[str]): The name of the LLM to load. Defaults to None.

    Returns:
        str: The model name for the specified LLM.

    Raises:
        ValueError: If the LLM configuration cannot be found or is invalid.
    """
    llm_config = load_llm_config(config, llm_name)
    model_name = llm_config.get("model")
    if not model_name:
        error_message = f"Model name not found in LLM configuration for '{llm_name}'"
        logger.error(error_message)
        raise ValueError(error_message)

    logger.debug(f"Retrieved model name '{model_name}' for LLM '{llm_name}'")
    return model_name

def load_and_validate_llm(config: Dict[str, Any], llm_name: Optional[str] = None) -> Dict[str, Any]:
    """
    Loads and validates the configuration for a specific LLM.

    Args:
        config (Dict[str, Any]): The full configuration dictionary.
        llm_name (Optional[str]): The name of the LLM to load. Defaults to None.

    Returns:
        Dict[str, Any]: The validated LLM configuration.

    Raises:
        ValueError: If validation fails.
    """
    logger.debug(f"Loading and validating LLM configuration for: {llm_name or 'unspecified'}")

    # Load the LLM configuration
    llm_config = load_llm_config(config, llm_name)

    # Validate the API keys
    validate_api_keys(config, llm_name)

    logger.debug(f"LLM configuration for '{llm_name}' is valid and loaded.")
    return llm_config

# # Example usage
# if __name__ == "__main__":
#     try:
#         config = load_server_config()
#         validate_mcp_server_env(config.get("mcpServers", {}))
#         llm_config = load_and_validate_llm(config, "default")
#         print("LLM Configuration:", redact_sensitive_data(llm_config))
#     except Exception as e:
#         logger.error(f"Error: {e}")