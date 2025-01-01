import os
import json
import logging
import re

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

def resolve_placeholders(value):
    """
    Resolves placeholders in the form of ${VAR_NAME} with the actual environment variable values.
    Raises a ValueError if the environment variable is not set.
    """
    if isinstance(value, str):
        pattern = re.compile(r'\$\{(\w+)\}')
        matches = pattern.findall(value)
        for var in matches:
            env_value = os.getenv(var)
            if env_value is None:
                logger.error(f"Environment variable '{var}' is not set but is required.")
                raise ValueError(f"Environment variable '{var}' is not set but is required.")
            value = value.replace(f"${{{var}}}", env_value)
    return value

def load_server_config(config_path):
    """
    Loads the server configuration from a JSON file and resolves placeholders.
    
    Args:
        config_path (str): Path to the JSON configuration file.
    
    Returns:
        dict: Processed configuration with placeholders resolved.
    """
    if not os.path.exists(config_path):
        logger.error(f'Configuration file not found at {config_path}')
        raise FileNotFoundError(f'Configuration file not found at {config_path}')
    
    with open(config_path, 'r') as f:
        try:
            config = json.load(f)
            logger.debug(f'Configuration loaded: {config}')
        except json.JSONDecodeError as e:
            logger.error(f'Invalid JSON in configuration file: {e}')
            raise
    
    # Resolve placeholders in llm_providers
    for profile, details in config.get('llm_providers', {}).items():
        api_key = details.get('api_key', '')
        resolved_api_key = resolve_placeholders(api_key)
        config['llm_providers'][profile]['api_key'] = resolved_api_key
    
    # Resolve placeholders in mcpServers' env variables
    for server, details in config.get('mcpServers', {}).items():
        env_vars = details.get('env', {})
        for var, value in env_vars.items():
            resolved_value = resolve_placeholders(value)
            config['mcpServers'][server]['env'][var] = resolved_value
    
    return config

def validate_api_keys(config, selected_llm):
    """
    Validates that all required API keys are present based on the selected LLM provider.
    
    Args:
        config (dict): The loaded and processed configuration.
        selected_llm (str): The selected LLM profile.
    
    Raises:
        ValueError: If any required API key is missing.
    
    Returns:
        dict: Configuration is assumed to be valid at this point.
    """
    llm_details = config['llm_providers'].get(selected_llm)
    if not llm_details:
        logger.error(f"Selected LLM profile '{selected_llm}' not found in configuration.")
        raise ValueError(f"Selected LLM profile '{selected_llm}' not found in configuration.")
    
    provider = llm_details.get('provider')
    api_key = llm_details.get('api_key', '')
    
    if provider != 'mock' and not api_key:
        logger.error(f"API key for provider '{provider}' in LLM profile '{selected_llm}' is missing.")
        raise ValueError(f"API key for provider '{provider}' in LLM profile '{selected_llm}' is missing.")
    
    # Validate MCP servers' environment variables are already resolved
    for server, details in config.get('mcpServers', {}).items():
        env_vars = details.get('env', {})
        for var, value in env_vars.items():
            if var.endswith('_API_KEY') and not value:
                logger.error(f"Environment variable '{var}' for server '{server}' is missing.")
                raise ValueError(f"Environment variable '{var}' for server '{server}' is missing.")
    
    logger.debug("All required API keys are present.")
    return config

def get_llm_provider(config, selected_llm):
    """
    Returns an instance of the selected LLM provider.
    
    Args:
        config (dict): The loaded and processed configuration.
        selected_llm (str): The selected LLM profile.
    
    Returns:
        LLMProvider: An instance of the selected LLM provider.
    """
    provider = config['llm_providers'][selected_llm]['provider']
    model = config['llm_providers'][selected_llm]['model']
    api_key = config['llm_providers'][selected_llm]['api_key']
    
    if provider == 'openai':
        from open_swarm_mcp.llm_providers.openai_llm import OpenAILLMProvider
        return OpenAILLMProvider(model=model, api_key=api_key)
    elif provider == 'grok':
        from open_swarm_mcp.llm_providers.grok_llm import GrokLLMProvider
        return GrokLLMProvider(model=model, api_key=api_key)
    elif provider == 'ollama':
        from open_swarm_mcp.llm_providers.ollama_llm import OllamaLLMProvider
        return OllamaLLMProvider(model=model)
    elif provider == 'mock':
        from open_swarm_mcp.llm_providers.mock_llm import MockLLMProvider
        return MockLLMProvider(model=model)
    else:
        logger.error(f"Unsupported LLM provider: {provider}")
        raise ValueError(f"Unsupported LLM provider: {provider}")

def are_required_mcp_servers_running(required_servers, config):
    """
    Checks if all required MCP servers are configured.
    
    Args:
        required_servers (list): List of required server names.
        config (dict): The loaded and processed configuration.
    
    Returns:
        tuple: (bool, list) where bool indicates all servers are running, and list contains missing servers.
    """
    configured_servers = config.get('mcpServers', {}).keys()
    missing_servers = [server for server in required_servers if server not in configured_servers]
    if missing_servers:
        logger.warning(f"Missing MCP servers: {missing_servers}")
        return False, missing_servers
    return True, []
