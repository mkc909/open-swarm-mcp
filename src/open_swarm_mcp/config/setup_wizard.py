# src/open_swarm_mcp/config/setup_wizard.py

import json
import os
import shlex
from typing import Any, Dict, Optional, List

from .config_loader import are_required_mcp_servers_running, LLM_PROVIDER_API_KEY_MAP
from open_swarm_mcp.utils.logger import setup_logger
from open_swarm_mcp.utils.color_utils import color_text, initialize_colorama

logger = setup_logger(__name__)

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def run_setup_wizard(config_path: str, blueprints_metadata: Dict[str, Dict[str, Any]], selected_blueprint: Optional[str] = None) -> Dict[str, Any]:
    """
    Interactive setup wizard to configure LLM settings, MCP servers, and optionally run a blueprint.
    
    Args:
        config_path (str): Path to the configuration file.
        blueprints_metadata (Dict[str, Dict[str, Any]]): Available blueprints metadata.
        selected_blueprint (Optional[str]): Specific blueprint to configure. If None, user selects interactively.
    
    Returns:
        Dict[str, Any]: Updated configuration dictionary.
    """
    initialize_colorama()
    
    print(color_text("\n=== Open Swarm MCP Setup Wizard ===\n", "cyan"))
    
    # Load existing config if available
    if os.path.exists(config_path):
        with open(config_path, "r") as f:
            config = json.load(f)
        print(color_text(f"Configuration file detected at '{config_path}'. Loading configuration.", "green"))
    else:
        config = {}
    
    # LLM Configuration
    llm = config.get("llm", {})
    
    print("Please provide the following LLM configurations:")
    
    # LLM Provider
    available_providers = list(LLM_PROVIDER_API_KEY_MAP.keys())
    default_provider = llm.get('provider', 'openai')
    prompt = f"LLM Provider ({', '.join(available_providers)}) [default: {default_provider}]: "
    llm_provider = input(prompt).strip().lower() or default_provider
    while llm_provider not in available_providers:
        print(color_text(f"Invalid provider. Please choose from {', '.join(available_providers)}.", "yellow"))
        llm_provider = input(prompt).strip().lower() or default_provider
    llm['provider'] = llm_provider
    
    # LLM Model
    default_model = llm.get('model', 'gpt-4')
    prompt = f"LLM Model Name [default: {default_model}]: "
    llm_model = input(prompt).strip() or default_model
    llm['model'] = llm_model
    
    # LLM API Key (from environment variables only)
    expected_api_key_env_var = LLM_PROVIDER_API_KEY_MAP.get(llm_provider, "LLM_API_KEY")
    llm_api_key = os.getenv(expected_api_key_env_var) or llm.get("api_key", "")
    if not llm_api_key:
        print(color_text(f"LLM API Key for provider '{llm_provider}' is not set in environment variables.", "yellow"))
        print(color_text(f"Please set the '{expected_api_key_env_var}' environment variable in your .env file.", "yellow"))
    else:
        llm['api_key'] = llm_api_key  # Only set it for runtime use
    
    # Temperature
    default_temp = llm.get('temperature', 0.2)
    prompt = f"LLM Temperature [default: {default_temp}]: "
    temperature_input = input(prompt).strip()
    try:
        temperature = float(temperature_input) if temperature_input else default_temp
    except ValueError:
        print(color_text("Invalid input for temperature. Using default value 0.2.", "yellow"))
        temperature = 0.2
    llm['temperature'] = temperature
    
    config['llm'] = llm
    
    # Blueprint Selection
    available_blueprints = list(blueprints_metadata.keys())
    if available_blueprints:
        if selected_blueprint and selected_blueprint in blueprints_metadata:
            blueprint_key = selected_blueprint
        else:
            print("\nAvailable Blueprints:")
            for idx, bp in enumerate(available_blueprints, start=1):
                metadata = blueprints_metadata[bp]
                title = metadata.get('title', 'No Title')
                description = metadata.get('description', 'No Description')
                print(f"{idx}. {bp}: {title} - {description}")
            
            while True:
                try:
                    bp_choice = int(input("\nEnter the number of the blueprint you want to configure (0 to skip): "))
                    if bp_choice == 0:
                        blueprint_key = None
                        break
                    elif 1 <= bp_choice <= len(available_blueprints):
                        blueprint_key = available_blueprints[bp_choice - 1]
                        break
                    else:
                        print(f"Please enter a number between 0 and {len(available_blueprints)}.")
                except ValueError:
                    print("Invalid input. Please enter a valid number.")
        
        if blueprint_key:
            blueprint_metadata = blueprints_metadata[blueprint_key]
            required_servers = blueprint_metadata.get("required_mcp_servers", [])
            
            print(color_text(f"\nConfiguring Blueprint: {blueprint_key} - {blueprint_metadata.get('title', '')}", "cyan"))
            print(f"Required MCP Servers: {', '.join(required_servers)}")
            
            # Configure each required MCP server
            mcp_servers = config.get("mcpServers", {})
            for server in required_servers:
                print(f"\nConfiguring MCP Server: {server}")
                
                server_config = mcp_servers.get(server, {})
                if not server_config:
                    server_config = {}
                    mcp_servers[server] = server_config
                
                # Command
                current_command = server_config.get("command", "")
                default_command = "uvx" if server != "brave-search" else "npx"
                prompt_cmd = f"Enter the command for '{server}' [default: {default_command}]: "
                user_command = input(prompt_cmd).strip() or default_command
                server_config["command"] = user_command
                
                # Args
                current_args = " ".join(server_config.get("args", [])) if "args" in server_config else ""
                default_args = blueprint_metadata.get("default_args", "")
                prompt_args = f"Enter the arguments for '{server}' [default: {default_args}]: "
                user_args_input = input(prompt_args).strip()
                if user_args_input:
                    new_args = shlex.split(user_args_input)
                    server_config["args"] = new_args
                else:
                    server_config["args"] = shlex.split(default_args)
                
                # Environment Variables
                env_vars = blueprint_metadata.get("env_vars", [])
                for env_var in env_vars:
                    env_value = server_config.get("env", {}).get(env_var, "")
                    if not env_value:
                        prompt_env = f"Enter the value for environment variable '{env_var}' (will be set as '{env_var}'): "
                        user_env_value = input(prompt_env).strip()
                        if user_env_value:
                            server_config.setdefault("env", {})[env_var] = user_env_value
                            # Suggest adding to .env file
                            add_to_env = input(f"Would you like to add '{env_var}' to your .env file? (yes/no): ").strip().lower()
                            if add_to_env in ['yes', 'y']:
                                try:
                                    with open(os.path.join(project_root, ".env"), "a") as env_file:
                                        env_file.write(f"\n{env_var}={user_env_value}\n")
                                    print(color_text(f"{env_var} has been added to your .env file.", "green"))
                                except Exception as e:
                                    logger.error(f"Failed to write to .env file: {e}")
                                    print(color_text(f"Failed to write to .env file. Please add '{env_var}' manually.", "red"))
                
                mcp_servers[server] = server_config
    
    # Save the updated configuration
    save_config_prompt = input("\nWould you like to save this configuration for future use? (yes/no): ").strip().lower()
    if save_config_prompt in ['yes', 'y']:
        try:
            with open(config_path, "w") as f:
                # Exclude sensitive API keys from being saved in the config file
                # They are managed via environment variables
                safe_config = config.copy()
                # Remove LLM API Key from config
                if 'api_key' in safe_config.get('llm', {}):
                    safe_config['llm']['api_key'] = ""
                # Remove MCP server API keys from env
                for srv in safe_config.get('mcpServers', {}):
                    if 'env' in safe_config['mcpServers'][srv]:
                        for env_var in safe_config['mcpServers'][srv]['env']:
                            safe_config['mcpServers'][srv]['env'][env_var] = ""
                json.dump(safe_config, f, indent=4)
            print(color_text("\nConfiguration has been saved successfully! Remember to set your API keys in the .env file.\n", "green"))
        except Exception as e:
            logger.error("Failed to save configuration: %s", str(e))
            print(color_text("Failed to save configuration. Please check permissions.", "red"))
    else:
        print("\nConfiguration not saved. It will need to be reconfigured next time.\n")

    return config
