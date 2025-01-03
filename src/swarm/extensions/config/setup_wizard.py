import json
import os
import shlex
from typing import Any, Dict, Optional

from swarm.extensions.config.config_loader import resolve_placeholders
from swarm.utils.logger import setup_logger
from swarm.utils.color_utils import color_text, initialize_colorama

logger = setup_logger(__name__)
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def run_setup_wizard(
    config_path: str,
    blueprints_metadata: Dict[str, Dict[str, Any]],
    selected_blueprint: Optional[str] = None
) -> Dict[str, Any]:
    """
    Interactive setup wizard to configure LLM settings, MCP servers, and optionally select a blueprint.

    Args:
        config_path (str): Path to the configuration file.
        blueprints_metadata (Dict[str, Dict[str, Any]]): Available blueprints metadata.
        selected_blueprint (Optional[str]): Specific blueprint to configure. If None, user selects interactively.

    Returns:
        Dict[str, Any]: Updated configuration dictionary.
    """
    initialize_colorama()

    print(color_text("\n=== Open Swarm Setup Wizard ===\n", "cyan"))

    # Load existing configuration or initialize a new one
    if os.path.exists(config_path):
        with open(config_path, "r") as f:
            config = json.load(f)
            config = resolve_placeholders(config)  # Resolve placeholders
            print(color_text(f"Configuration file detected at '{config_path}'. Loading configuration.", "green"))
    else:
        config = {"llm": {}, "mcpServers": {}}
        print(color_text("No configuration file found. Starting with a new configuration.", "yellow"))

    # LLM Configuration
    llm = config.get("llm", {})
    print("Configuring LLM settings:")

    # Load LLM providers from MCP server config
    llm_providers = _load_swarm_config()["llm"]
    provider_names = list(llm_providers.keys())
    default_provider = llm.get("provider", provider_names[0])
    llm_provider = input(f"Select LLM Provider [{default_provider}]: ").strip() or default_provider
    while llm_provider not in provider_names:
        print(color_text(f"Invalid provider. Choose from: {', '.join(provider_names)}", "yellow"))
        llm_provider = input(f"Select LLM Provider [{default_provider}]: ").strip() or default_provider
    llm["provider"] = llm_provider

    llm["model"] = input("Enter Model Name (e.g., gpt-4): ").strip() or llm.get("model", "gpt-4")
    llm["temperature"] = float(input("Enter Temperature (default 0.7): ") or llm.get("temperature", 0.7))

    # Validate API key
    api_key_placeholder = llm_providers[llm_provider]["api_key"]
    api_key = os.getenv(api_key_placeholder.strip("${}"))
    if not api_key:
        print(color_text(f"API Key for '{llm_provider}' not set in environment. Set {api_key_placeholder} in .env.", "yellow"))
    llm["api_key"] = ""  # Do not store sensitive keys
    config["llm"] = llm

    # Blueprint Configuration
    if blueprints_metadata:
        print("\nAvailable Blueprints:")
        for idx, (key, metadata) in enumerate(blueprints_metadata.items(), start=1):
            print(f"{idx}. {key}: {metadata.get('title', 'No Title')} - {metadata.get('description', 'No Description')}")

        selected_index = int(input("\nSelect a Blueprint (0 to skip): ") or 0)
        if selected_index > 0 and selected_index <= len(blueprints_metadata):
            blueprint_key = list(blueprints_metadata.keys())[selected_index - 1]
            blueprint = blueprints_metadata[blueprint_key]
            required_servers = blueprint.get("required_mcp_servers", [])
            print(color_text(f"\nConfiguring Blueprint: {blueprint_key}", "cyan"))
            print(f"Required MCP Servers: {', '.join(required_servers)}")

            # Configure MCP servers
            for server in required_servers:
                server_config = config["mcpServers"].get(server, {})
                print(f"\nConfiguring MCP Server: {server}")

                server_config["command"] = input(f"Command [{server_config.get('command', '')}]: ") or server_config.get("command", "")
                server_config["args"] = shlex.split(input(f"Arguments [{', '.join(server_config.get('args', []))}]: ") or "")

                # Configure environment variables
                server_env = server_config.get("env", {})
                for env_var in blueprint.get("env_vars", []):
                    env_value = server_env.get(env_var) or input(f"Enter value for '{env_var}': ").strip()
                    server_env[env_var] = env_value
                server_config["env"] = server_env
                config["mcpServers"][server] = server_config

    # Save the configuration
    save_choice = input("Save Configuration? (yes/no): ").strip().lower() in ["yes", "y"]
    if save_choice:
        with open(config_path, "w") as f:
            safe_config = config.copy()
            safe_config["llm"]["api_key"] = ""  # Strip sensitive data
            json.dump(safe_config, f, indent=4)
        print(color_text(f"Configuration saved to {config_path}.", "green"))
    else:
        print(color_text("Configuration not saved.", "red"))

    return config

def _load_swarm_config() -> Dict[str, Any]:
    """Load the swarm configuration from the default path."""
    config_path = "mcp_server_config.json"
    try:
        with open(config_path, "r") as file:
            config = json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        # Return a default configuration if the file is missing or invalid
        config = {
            "llm": {
                "ollama": {
                    "provider": "openai",
                    "model": "llama3.2:latest",
                    "base_url": "http://localhost:11434/",
                    "api_key": "",
                    "temperature": 0.0
                }
            }
        }
    return config