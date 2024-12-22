import argparse
import asyncio
import json
import logging
import os
import sys
import pkgutil
import importlib
import shlex
import random
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv

# Add the project root to sys.path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Load environment variables
load_dotenv(dotenv_path=os.path.join(project_root, ".env"))

# Import custom modules with corrected paths
from open_swarm_mcp.utils.logger import setup_logger
from open_swarm_mcp.config.setup_wizard import run_setup_wizard
from open_swarm_mcp.config.config_loader import (
    load_server_config,
    validate_api_keys,
    are_required_mcp_servers_running,
)
from open_swarm_mcp.modes.cli_mode import run_cli_mode
from open_swarm_mcp.modes.rest_mode import run_rest_mode
# from open_swarm_mcp.modes.mcp_host_mode import run_mcp_host_mode
from open_swarm_mcp.agent.agent_builder import build_agent_with_mcp_tools
from open_swarm_mcp.utils.color_utils import color_text, initialize_colorama

# Initialize logger
logger = setup_logger(__name__)

# Mapping of LLM providers to their respective API key environment variables
LLM_PROVIDER_API_KEY_MAP = {
    "openai": "OPENAI_API_KEY",
    "ollama": "OLLAMA_API_KEY",
    # Add other providers and their API key environment variables here
}

def parse_arguments():
    """
    Parse command-line arguments for dynamic LLM configuration and other overrides.
    """
    parser = argparse.ArgumentParser(description="Run Open Swarm MCP in various modes.")
    parser.add_argument(
        "--config",
        type=str,
        default=os.path.join(project_root, "mcp_server_config.json"),
        help="Path to the MCP server configuration file."
    )
    parser.add_argument(
        "--llm-provider",
        type=str,
        default=None,
        choices=list(LLM_PROVIDER_API_KEY_MAP.keys()),
        help="Override the LLM provider (e.g., 'openai', 'ollama')."
    )
    parser.add_argument(
        "--llm-model",
        type=str,
        default=None,
        help="Override the LLM model name."
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=None,
        help="Override the LLM temperature setting."
    )
    parser.add_argument(
        "--mode",
        type=str,
        default="cli",
        choices=["cli", "rest", "mcp-service"],
        help="Specify the operational mode: 'cli', 'rest', or 'mcp-service'."
    )
    parser.add_argument(
        "--blueprint",
        type=str,
        help="Specify the blueprint to run using dot notation (e.g., 'basic.default')."
    )
    parser.add_argument(
        "--setup",
        action='store_true',
        help="Re-run the setup wizard regardless of existing configuration."
    )
    return parser.parse_args()

def discover_blueprints(blueprints_path: str) -> Dict[str, Dict[str, Any]]:
    """
    Discover all blueprint modules in the given directory and extract their metadata.
    
    Args:
        blueprints_path (str): Path to the blueprints directory.
    
    Returns:
        Dict[str, Dict[str, Any]]: Mapping of 'category.blueprint_name' to their metadata.
    """
    blueprints_metadata = {}
    if not os.path.isdir(blueprints_path):
        logger.error(f"Blueprints directory not found: {blueprints_path}")
        return blueprints_metadata

    # Iterate over categories
    for category_finder, category_name, ispkg in pkgutil.iter_modules([blueprints_path]):
        if ispkg:
            category_path = os.path.join(blueprints_path, category_name)
            # Iterate over blueprints within the category
            for blueprint_finder, blueprint_name, blueprint_ispkg in pkgutil.iter_modules([category_path]):
                if blueprint_ispkg:
                    try:
                        # Construct the module name based on the new blueprint naming convention
                        module_name = f"open_swarm_mcp.blueprints.{category_name}.{blueprint_name}.blueprint_{blueprint_name}"
                        module = importlib.import_module(module_name)
                        metadata = getattr(module, "EXAMPLE_METADATA", None)
                        if metadata:
                            key = f"{category_name}.{blueprint_name}"
                            blueprints_metadata[key] = metadata
                        else:
                            logger.warning(f"No EXAMPLE_METADATA found in {module_name}")
                    except Exception as e:
                        logger.error(f"Error loading blueprint '{category_name}/{blueprint_name}': {e}")
    return blueprints_metadata

def discover_blueprints_metadata() -> Dict[str, Dict[str, Any]]:
    """
    Discover all blueprints and collect their metadata.
    
    Returns:
        Dict[str, Dict[str, Any]]: Mapping of 'category.blueprint_name' to their metadata.
    """
    blueprints_path = os.path.join(os.path.dirname(__file__), "blueprints")
    return discover_blueprints(blueprints_path)

def merge_llm_config(config: Dict[str, Any], args: argparse.Namespace) -> Dict[str, Any]:
    """
    Merge LLM overrides from command-line arguments into the configuration.

    Args:
        config (Dict[str, Any]): Original configuration.
        args (argparse.Namespace): Parsed command-line arguments.

    Returns:
        Dict[str, Any]: Updated configuration with overrides.
    """
    llm_config = config.get("llm", {})
    if args.llm_provider:
        llm_config["provider"] = args.llm_provider
    if args.llm_model:
        llm_config["model"] = args.llm_model
    if args.temperature is not None:
        llm_config["temperature"] = args.temperature

    config["llm"] = llm_config
    logger.debug("Final LLM configuration: %s", llm_config)
    return config

async def configure_missing_mcp_servers(missing_servers: List[str], config: Dict[str, Any], blueprint_metadata: Dict[str, Any]) -> Dict[str, Any]:
    """
    Configure missing MCP servers dynamically based on blueprint metadata.
    """
    mcp_servers = config.get("mcpServers", {})
    for server in missing_servers:
        print(color_text(f"\nConfiguring MCP Server: {server}", "cyan"))
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

    config['mcpServers'] = mcp_servers
    return config

def save_configuration(config_path: str, config: Dict[str, Any]):
    """
    Save the updated configuration to the config file, excluding sensitive API keys.
    """
    try:
        safe_config = config.copy()
        # Remove LLM API Key from config
        if 'api_key' in safe_config.get('llm', {}):
            safe_config['llm']['api_key'] = ""
        # Remove MCP server API keys from env
        for srv in safe_config.get('mcpServers', {}):
            if 'env' in safe_config['mcpServers'][srv]:
                for env_var in safe_config['mcpServers'][srv]['env']:
                    safe_config['mcpServers'][srv]['env'][env_var] = ""
        with open(config_path, "w") as f:
            json.dump(safe_config, f, indent=4)
        print(color_text("\nConfiguration has been saved successfully! Remember to set your API keys in the .env file.\n", "green"))
    except Exception as e:
        logger.error("Failed to save configuration: %s", str(e))
        print(color_text("Failed to save configuration. Please check permissions.", "red"))

async def run_blueprint_mode(blueprint: str, config: Dict[str, Any], blueprints_metadata: Dict[str, Dict[str, Any]], args: argparse.Namespace):
    """
    Run a specified blueprint.
    """
    if blueprint not in blueprints_metadata:
        logger.error(f"Blueprint '{blueprint}' not found.")
        print(color_text(f"Blueprint '{blueprint}' not found.", "red"))
        return

    blueprint_metadata = blueprints_metadata[blueprint]
    required_servers = blueprint_metadata.get("required_mcp_servers", [])

    all_running, missing_servers = are_required_mcp_servers_running(required_servers, config)
    if not all_running:
        print(color_text(
            f"\nBlueprint '{blueprint}' requires the following MCP servers to be configured: {', '.join(required_servers)}", 
            "yellow"
        ))
        print(color_text(
            "Some required MCP servers are missing or improperly configured.", 
            "yellow"
        ))
        configure_missing = input("Would you like to configure the missing MCP servers now? (yes/no): ").strip().lower()
        if configure_missing in ['yes', 'y']:
            config = await configure_missing_mcp_servers(missing_servers, config, blueprint_metadata)
            save_configuration(args.config, config)
        else:
            print(color_text("Cannot proceed without configuring the required MCP servers.", "red"))
            return

    try:
        agent = await build_agent_with_mcp_tools(config)
    except Exception as e:
        logger.error(f"Failed to build agent: {e}")
        print(color_text(f"Failed to build agent: {e}", "red"))
        return

    if args.mode == "rest":
        await run_rest_mode(agent)
    elif args.mode == "mcp-service":
        # await run_mcp_host_mode(agent)
        logger.error("MCP host mode is not implemented yet")
        print(color_text("MCP host mode is not implemented yet", "red"))
    else:
        # Default to CLI mode if not specified
        await run_cli_mode(agent, colorama_available=True)

async def handle_blueprint_selection(config: Dict[str, Any], blueprints_metadata: Dict[str, Dict[str, Any]], args: argparse.Namespace) -> Optional[str]:
    """
    Handle the blueprint selection process in CLI mode.
    
    Returns:
        Optional[str]: Selected blueprint name or "basic.default" if default is chosen.
    """
    available_blueprints = list(blueprints_metadata.keys())
    if not available_blueprints:
        print(color_text("No blueprints available. Using default blueprint.", "yellow"))
        return "basic.default"

    print("Available Blueprints:")
    for idx, bp in enumerate(available_blueprints, start=1):
        metadata = blueprints_metadata[bp]
        title = metadata.get('title', 'No Title')
        description = metadata.get('description', 'No Description')
        print(f"{idx}. {bp}: {title} - {description}")

    while True:
        try:
            bp_choice = int(input("\nEnter the number of the blueprint you want to use (0 to use default): "))
            if bp_choice == 0:
                return "basic.default"  # Use the default blueprint
            elif 1 <= bp_choice <= len(available_blueprints):
                blueprint = available_blueprints[bp_choice - 1]
                return blueprint
            print(f"Please enter a number between 0 and {len(available_blueprints)}.")
        except ValueError:
            print("Invalid input. Please enter a valid number.")

async def main():
    """
    Main entry point for the Open Swarm MCP application.
    """
    initialize_colorama()
    args = parse_arguments()
    blueprints_metadata = discover_blueprints_metadata()

    # Handle configuration setup
    if args.setup:
        config = run_setup_wizard(args.config, blueprints_metadata)
    else:
        try:
            config = load_server_config(args.config)
            print(color_text(f"\nConfiguration file detected at '{args.config}'. Loading configuration.", "green"))
        except (FileNotFoundError, json.JSONDecodeError):
            logger.warning("Configuration issue. Launching setup wizard.")
            config = run_setup_wizard(args.config, blueprints_metadata)
        else:
            config = merge_llm_config(config, args)
            try:
                config = validate_api_keys(config)
            except Exception as e:
                logger.warning(f"Configuration incomplete: {e}")
                config = run_setup_wizard(args.config, blueprints_metadata)

    # Handle LLM API key setup
    llm_config = config.get("llm", {})
    llm_provider = llm_config.get("provider", "openai")
    expected_api_key_env_var = LLM_PROVIDER_API_KEY_MAP.get(llm_provider, "LLM_API_KEY")

    llm_api_key = os.getenv(expected_api_key_env_var)
    if llm_api_key:
        config['llm']['api_key'] = llm_api_key  # Temporarily set it for runtime use
        logger.info(f"LLM API Key loaded from environment variable '{expected_api_key_env_var}'.")
    else:
        print(color_text(
            f"LLM API Key is missing. Please set the '{expected_api_key_env_var}' environment variable.", 
            "yellow"
        ))
        logger.warning(f"LLM API Key is missing. Please set the '{expected_api_key_env_var}' environment variable.")

    # Reload configuration after potential updates
    try:
        config = load_server_config(args.config)
        config = merge_llm_config(config, args)
        config = validate_api_keys(config)
    except Exception as e:
        logger.error("Failed to load configuration after setup: %s", str(e))
        print(color_text(f"Failed to load configuration: {e}", "red"))
        return

    # Get blueprint from args or environment
    blueprint = args.blueprint or os.getenv("SWARM_BLUEPRINT")

    # Handle different operational modes
    if args.mode in ["rest", "mcp-service"]:
        if not blueprint:
            logger.error("No blueprint specified. Use --blueprint or set SWARM_BLUEPRINT environment variable.")
            print(color_text("No blueprint specified. Use --blueprint or set SWARM_BLUEPRINT environment variable.", "red"))
            delay = 60 + random.randint(0, 60)
            logger.info(f"Delaying exit for {delay} seconds.")
            await asyncio.sleep(delay)
            return
        
        await run_blueprint_mode(blueprint, config, blueprints_metadata, args)
    
    elif args.mode == "cli":
        if not blueprint:
            print(color_text("\nNo blueprint specified. Launching the setup wizard to select a blueprint.\n", "cyan"))
            config = run_setup_wizard(args.config, blueprints_metadata)
            blueprint = await handle_blueprint_selection(config, blueprints_metadata, args)

        if blueprint:
            # Verify blueprint requirements
            blueprint_metadata = blueprints_metadata.get(blueprint, {})
            required_servers = blueprint_metadata.get("required_mcp_servers", [])
            all_running, missing_servers = are_required_mcp_servers_running(required_servers, config)
            
            if not all_running:
                print(color_text(
                    f"\nBlueprint '{blueprint}' requires the following MCP servers to be configured: {', '.join(required_servers)}", 
                    "yellow"
                ))
                print(color_text(
                    "Some required MCP servers are missing or improperly configured.", 
                    "yellow"
                ))
                configure_missing = input("Would you like to configure the missing MCP servers now? (yes/no): ").strip().lower()
                if configure_missing in ['yes', 'y']:
                    config = await configure_missing_mcp_servers(missing_servers, config, blueprint_metadata)
                    save_configuration(args.config, config)
                else:
                    print(color_text("Cannot proceed without configuring the required MCP servers.", "red"))
                    blueprint = None

        # Run CLI mode with or without blueprint
        try:
            agent = await build_agent_with_mcp_tools(config)
            await run_cli_mode(agent, colorama_available=True)
        except Exception as e:
            logger.error("Fatal error: %s", str(e))
            print(color_text(f"Fatal error: {e}", "red"))
    
    else:
        logger.error(f"Unsupported mode: {args.mode}")
        print(color_text(f"Unsupported mode: {args.mode}", "red"))

def handle_shutdown():
    """
    Perform cleanup operations before shutdown.
    """
    logger.info("Shutting down Open Swarm MCP...")
    # Add any cleanup operations here

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nReceived shutdown signal (Ctrl+C)")
        handle_shutdown()
    except Exception as e:
        logger.error("Unhandled exception: %s", str(e))
        print(color_text(f"\nFatal error: {e}", "red"))
        handle_shutdown()
        sys.exit(1)
    finally:
        sys.exit(0)
