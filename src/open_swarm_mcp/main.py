# src/open_swarm_mcp/main.py

import argparse
import asyncio
import json
import logging
import os
import sys
import importlib.util
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv

# Add the project root to sys.path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
    logging.debug(f"Added '{project_root}' to sys.path")

# Load environment variables from the project root
dotenv_path = os.path.join(project_root, ".env")
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path=dotenv_path)
    logging.debug(f"Loaded environment variables from '{dotenv_path}'")
else:
    logging.warning(f"'.env' file not found at '{dotenv_path}'")

# Import custom modules with corrected paths
try:
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
    logging.debug("Successfully imported custom modules")
except ImportError as e:
    logging.error(f"Error importing custom modules: {e}")
    sys.exit(1)

# Initialize logger
logger = setup_logger(__name__)
logger.info("Logger initialized")

# Mapping of LLM providers to their respective API key environment variables
LLM_PROVIDER_API_KEY_MAP = {
    "openai": "OPENAI_API_KEY",
    "ollama": "OLLAMA_API_KEY",
    # Add other providers and their API key environment variables here
}

def parse_arguments() -> argparse.Namespace:
    """
    Parse command-line arguments for dynamic LLM configuration and other overrides.

    Returns:
        argparse.Namespace: Parsed command-line arguments.
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
        help="Specify the blueprint to run (e.g., 'sqlite_and_search')."
    )
    parser.add_argument(
        "--setup",
        action='store_true',
        help="Re-run the setup wizard regardless of existing configuration."
    )
    args = parser.parse_args()
    logger.debug(f"Parsed arguments: {args}")
    return args

def discover_blueprints(blueprints_path: str) -> Dict[str, Dict[str, Any]]:
    """
    Discover all blueprint modules in the given directory and extract their metadata.

    Args:
        blueprints_path (str): Path to the blueprints directory.

    Returns:
        Dict[str, Dict[str, Any]]: Mapping of 'blueprint_name' to their metadata.
    """
    blueprints_metadata = {}
    logger.debug(f"Starting discovery of blueprints in '{blueprints_path}'")

    if not os.path.isdir(blueprints_path):
        logger.error(f"Blueprints directory not found: {blueprints_path}")
        return blueprints_metadata

    # Iterate over blueprint directories
    for blueprint_dir in os.listdir(blueprints_path):
        full_dir_path = os.path.join(blueprints_path, blueprint_dir)
        if os.path.isdir(full_dir_path):
            blueprint_module_filename = f"blueprint_{blueprint_dir}.py"
            blueprint_module_path = os.path.join(full_dir_path, blueprint_module_filename)

            if os.path.isfile(blueprint_module_path):
                logger.debug(f"Found blueprint module: {blueprint_module_path}")
                try:
                    # Dynamically load the blueprint module
                    spec = importlib.util.spec_from_file_location(
                        f"blueprints.{blueprint_dir}.blueprint_{blueprint_dir}",
                        blueprint_module_path
                    )
                    if spec and spec.loader:
                        module = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(module)
                        metadata = getattr(module, "EXAMPLE_METADATA", None)
                        if metadata:
                            blueprints_metadata[blueprint_dir] = metadata
                            logger.info(f"Discovered blueprint '{blueprint_dir}': {metadata}")
                        else:
                            logger.warning(f"No EXAMPLE_METADATA found in {blueprint_module_path}")
                    else:
                        logger.warning(f"Could not load module spec for {blueprint_module_path}")
                except Exception as e:
                    logger.error(f"Error loading blueprint '{blueprint_dir}': {e}")
            else:
                logger.warning(f"Blueprint module '{blueprint_module_filename}' not found in '{blueprint_dir}'")
        else:
            logger.debug(f"Skipping non-directory item in blueprints: '{blueprint_dir}'")

    logger.debug(f"Blueprint discovery completed. Total blueprints found: {len(blueprints_metadata)}")
    return blueprints_metadata

def discover_blueprints_metadata() -> Dict[str, Dict[str, Any]]:
    """
    Discover all blueprints and collect their metadata.

    Returns:
        Dict[str, Dict[str, Any]]: Mapping of 'blueprint_name' to their metadata.
    """
    blueprints_path = os.path.join(project_root, "blueprints")
    logger.debug(f"Blueprints path set to '{blueprints_path}'")
    blueprints_metadata = discover_blueprints(blueprints_path)
    logger.debug(f"Discovered blueprints metadata: {blueprints_metadata}")
    return blueprints_metadata

def merge_llm_config(config: Dict[str, Any], args: argparse.Namespace) -> Dict[str, Any]:
    """
    Merge LLM overrides from command-line arguments into the configuration.

    Args:
        config (Dict[str, Any]): Original configuration.
        args (argparse.Namespace): Parsed command-line arguments.

    Returns:
        Dict[str, Any]: Updated configuration with overrides.
    """
    logger.debug("Merging LLM configuration from command-line arguments")
    llm_config = config.get("llm", {})
    if args.llm_provider:
        llm_config["provider"] = args.llm_provider
        logger.info(f"Overridden LLM provider: {args.llm_provider}")
    if args.llm_model:
        llm_config["model"] = args.llm_model
        logger.info(f"Overridden LLM model: {args.llm_model}")
    if args.temperature is not None:
        llm_config["temperature"] = args.temperature
        logger.info(f"Overridden LLM temperature: {args.temperature}")

    config["llm"] = llm_config
    logger.debug(f"Final LLM configuration after merge: {llm_config}")
    return config

async def configure_missing_mcp_servers(
    missing_servers: List[str],
    config: Dict[str, Any],
    blueprint_metadata: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Configure missing MCP servers dynamically based on blueprint metadata.

    Args:
        missing_servers (List[str]): List of missing MCP server names.
        config (Dict[str, Any]): Current configuration dictionary.
        blueprint_metadata (Dict[str, Any]): Metadata of the current blueprint.

    Returns:
        Dict[str, Any]: Updated configuration dictionary with missing MCP servers configured.
    """
    logger.debug(f"Configuring missing MCP servers: {missing_servers}")
    mcp_servers = config.get("mcpServers", {})
    for server in missing_servers:
        logger.info(f"Configuring MCP Server: {server}")
        print(color_text(f"\nConfiguring MCP Server: {server}", "cyan"))
        server_config = mcp_servers.get(server, {})
        if not server_config:
            server_config = {}
            mcp_servers[server] = server_config
            logger.debug(f"Initialized configuration for MCP server '{server}'")

        # Command
        current_command = server_config.get("command", "")
        default_command = "uvx" if server != "brave-search" else "npx"
        prompt_cmd = f"Enter the command for '{server}' [default: {default_command}]: "
        user_command = input(prompt_cmd).strip() or default_command
        server_config["command"] = user_command
        logger.debug(f"Set command for MCP server '{server}': {user_command}")

        # Args
        default_args = blueprint_metadata.get("default_args", "")
        prompt_args = f"Enter the arguments for '{server}' [default: {default_args}]: "
        user_args_input = input(prompt_args).strip()
        if user_args_input:
            new_args = shlex.split(user_args_input)
            server_config["args"] = new_args
            logger.debug(f"Set custom args for MCP server '{server}': {new_args}")
        else:
            server_config["args"] = shlex.split(default_args)
            logger.debug(f"Set default args for MCP server '{server}': {server_config['args']}")

        # Environment Variables
        env_vars = blueprint_metadata.get("env_vars", [])
        for env_var in env_vars:
            env_value = server_config.get("env", {}).get(env_var, "")
            if not env_value:
                prompt_env = f"Enter the value for environment variable '{env_var}' (will be set as '{env_var}'): "
                user_env_value = input(prompt_env).strip()
                if user_env_value:
                    server_config.setdefault("env", {})[env_var] = user_env_value
                    logger.debug(f"Set environment variable '{env_var}' for MCP server '{server}': {user_env_value}")
                    add_to_env = input(f"Would you like to add '{env_var}' to your .env file? (yes/no): ").strip().lower()
                    if add_to_env in ['yes', 'y']:
                        try:
                            with open(os.path.join(project_root, ".env"), "a") as env_file:
                                env_file.write(f"\n{env_var}={user_env_value}\n")
                            print(color_text(f"{env_var} has been added to your .env file.", "green"))
                            logger.info(f"Added environment variable '{env_var}' to '.env' file")
                        except Exception as e:
                            logger.error(f"Failed to write to .env file: {e}")
                            print(color_text(f"Failed to write to .env file. Please add '{env_var}' manually.", "red"))

        mcp_servers[server] = server_config
        logger.debug(f"Updated configuration for MCP server '{server}': {server_config}")

    config['mcpServers'] = mcp_servers
    logger.info("Completed configuration of missing MCP servers")
    return config

def save_configuration(config_path: str, config: Dict[str, Any]):
    """
    Save the updated configuration to the config file, excluding sensitive API keys.

    Args:
        config_path (str): Path to the configuration file.
        config (Dict[str, Any]): Configuration dictionary to save.
    """
    logger.debug(f"Saving configuration to '{config_path}'")
    try:
        safe_config = config.copy()
        # Remove LLM API Key from config
        if 'api_key' in safe_config.get('llm', {}):
            safe_config['llm']['api_key'] = ""
            logger.debug("Removed LLM API key from configuration for security")
        # Remove MCP server API keys from env
        for srv in safe_config.get('mcpServers', {}):
            if 'env' in safe_config['mcpServers'][srv]:
                for env_var in safe_config['mcpServers'][srv]['env']:
                    safe_config['mcpServers'][srv]['env'][env_var] = ""
                    logger.debug(f"Removed MCP server environment variable '{env_var}' from configuration for security")
        with open(config_path, "w") as f:
            json.dump(safe_config, f, indent=4)
        print(color_text("\nConfiguration has been saved successfully! Remember to set your API keys in the .env file.\n", "green"))
        logger.info(f"Configuration saved to '{config_path}'")
    except Exception as e:
        logger.error(f"Failed to save configuration: {e}")
        print(color_text("Failed to save configuration. Please check permissions.", "red"))

async def run_blueprint_mode(
    blueprint: str,
    config: Dict[str, Any],
    blueprints_metadata: Dict[str, Dict[str, Any]],
    args: argparse.Namespace
):
    """
    Run a specified blueprint.

    Args:
        blueprint (str): The blueprint to run (e.g., 'sqlite_and_search').
        config (Dict[str, Any]): Configuration dictionary.
        blueprints_metadata (Dict[str, Dict[str, Any]]): Metadata of all discovered blueprints.
        args (argparse.Namespace): Parsed command-line arguments.
    """
    logger.debug(f"Running blueprint mode with blueprint '{blueprint}'")
    if blueprint not in blueprints_metadata:
        logger.error(f"Blueprint '{blueprint}' not found.")
        print(color_text(f"Blueprint '{blueprint}' not found.", "red"))
        return

    blueprint_metadata = blueprints_metadata[blueprint]
    logger.debug(f"Blueprint metadata for '{blueprint}': {blueprint_metadata}")
    required_servers = blueprint_metadata.get("required_mcp_servers", [])
    logger.debug(f"Blueprint '{blueprint}' requires MCP servers: {required_servers}")

    all_running, missing_servers = are_required_mcp_servers_running(required_servers, config)
    logger.debug(f"Are all required MCP servers running? {all_running}")
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
        logger.debug(f"User chose to configure missing MCP servers: {configure_missing}")
        if configure_missing in ['yes', 'y']:
            config = await configure_missing_mcp_servers(missing_servers, config, blueprint_metadata)
            save_configuration(args.config, config)
        else:
            print(color_text("Cannot proceed without configuring the required MCP servers.", "red"))
            logger.warning("User declined to configure missing MCP servers")
            return

    try:
        logger.debug("Building agent with MCP tools")
        agent = await build_agent_with_mcp_tools(config)
        logger.info("Agent built successfully with MCP tools")
    except Exception as e:
        logger.error(f"Failed to build agent: {e}")
        print(color_text(f"Failed to build agent: {e}", "red"))
        return

    if args.mode == "rest":
        logger.debug("Running in REST mode")
        await run_rest_mode(agent)
    elif args.mode == "mcp-service":
        # await run_mcp_host_mode(agent)
        logger.error("MCP host mode is not implemented yet")
        print(color_text("MCP host mode is not implemented yet", "red"))
    else:
        logger.debug("Running in CLI mode")
        await run_cli_mode(agent, colorama_available=True)

async def handle_blueprint_selection(
    config: Dict[str, Any],
    blueprints_metadata: Dict[str, Dict[str, Any]],
    args: argparse.Namespace
) -> Optional[str]:
    """
    Handle the blueprint selection process in CLI mode.

    Args:
        config (Dict[str, Any]): Current configuration dictionary.
        blueprints_metadata (Dict[str, Dict[str, Any]]): Metadata of all discovered blueprints.
        args (argparse.Namespace): Parsed command-line arguments.

    Returns:
        Optional[str]: Selected blueprint name or "basic.default" if default is chosen.
    """
    logger.debug("Handling blueprint selection")
    available_blueprints = list(blueprints_metadata.keys())
    if not available_blueprints:
        logger.warning("No blueprints available. Using default blueprint.")
        print(color_text("No blueprints available. Using default blueprint.", "yellow"))
        return "basic.default"

    print("Available Blueprints:")
    for idx, bp in enumerate(available_blueprints, start=1):
        metadata = blueprints_metadata[bp]
        title = metadata.get('title', 'No Title')
        description = metadata.get('description', 'No Description')
        print(f"{idx}. {bp}: {title} - {description}")
        logger.debug(f"Listed blueprint {idx}: {bp} - {title}")

    while True:
        try:
            bp_choice_input = input("\nEnter the number of the blueprint you want to use (0 to use default): ")
            logger.debug(f"User input for blueprint selection: '{bp_choice_input}'")
            bp_choice = int(bp_choice_input)
            if bp_choice == 0:
                logger.info("User chose to use default blueprint 'basic.default'")
                return "basic.default"  # Use the default blueprint
            elif 1 <= bp_choice <= len(available_blueprints):
                blueprint = available_blueprints[bp_choice - 1]
                logger.info(f"User selected blueprint: '{blueprint}'")
                return blueprint
            else:
                print(f"Please enter a number between 0 and {len(available_blueprints)}.")
                logger.warning(f"User entered invalid blueprint number: {bp_choice}")
        except ValueError:
            print("Invalid input. Please enter a valid number.")
            logger.warning("User entered non-integer value for blueprint selection")

async def main():
    """
    Main entry point for the Open Swarm MCP application.
    """
    initialize_colorama()
    logger.debug("Starting main application")
    args = parse_arguments()
    logger.debug(f"Command-line arguments: {args}")
    blueprints_metadata = discover_blueprints_metadata()
    logger.debug(f"Discovered blueprints metadata: {blueprints_metadata}")

    # Handle configuration setup
    if args.setup:
        logger.info("Setup flag detected. Running setup wizard.")
        config = run_setup_wizard(args.config, blueprints_metadata)
    else:
        try:
            config = load_server_config(args.config)
            logger.info(f"Configuration file detected at '{args.config}'. Loading configuration.")
            logger.debug(f"Loaded configuration: {config}")
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.warning(f"Configuration issue ({e}). Launching setup wizard.")
            config = run_setup_wizard(args.config, blueprints_metadata)
        else:
            config = merge_llm_config(config, args)
            logger.debug(f"Configuration after merging LLM overrides: {config}")
            try:
                config = validate_api_keys(config)
                logger.info("Configuration validated with API keys.")
            except Exception as e:
                logger.warning(f"Configuration incomplete ({e}). Launching setup wizard.")
                config = run_setup_wizard(args.config, blueprints_metadata)

    # Handle LLM API key setup
    llm_config = config.get("llm", {})
    llm_provider = llm_config.get("provider", "openai")
    expected_api_key_env_var = LLM_PROVIDER_API_KEY_MAP.get(llm_provider, "LLM_API_KEY")
    logger.debug(f"LLM provider: {llm_provider}")
    llm_api_key = os.getenv(expected_api_key_env_var)
    logger.debug(f"LLM API Key from environment: {'set' if llm_api_key else 'not set'}")

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
        logger.debug(f"Reloaded configuration: {config}")
        config = merge_llm_config(config, args)
        logger.debug(f"Configuration after merging LLM overrides: {config}")
        config = validate_api_keys(config)
        logger.info("Configuration validated after reloading.")
    except Exception as e:
        logger.error(f"Failed to load configuration after setup: {e}")
        print(color_text(f"Failed to load configuration: {e}", "red"))
        return

    # Get blueprint from args or environment
    blueprint = args.blueprint or os.getenv("SWARM_BLUEPRINT")
    logger.debug(f"Blueprint specified via args or environment: '{blueprint}'")

    # Handle different operational modes
    if args.mode in ["rest", "mcp-service"]:
        logger.debug(f"Operating in '{args.mode}' mode")
        if not blueprint:
            logger.error("No blueprint specified. Use --blueprint or set SWARM_BLUEPRINT environment variable.")
            print(color_text("No blueprint specified. Use --blueprint or set SWARM_BLUEPRINT environment variable.", "red"))
            delay = 60 + random.randint(0, 60)
            logger.info(f"Delaying exit for {delay} seconds.")
            await asyncio.sleep(delay)
            return

        await run_blueprint_mode(blueprint, config, blueprints_metadata, args)

    elif args.mode == "cli":
        logger.debug("Operating in 'cli' mode")
        if not blueprint:
            print(color_text("\nNo blueprint specified. Launching the setup wizard to select a blueprint.\n", "cyan"))
            config = run_setup_wizard(args.config, blueprints_metadata)
            blueprint = await handle_blueprint_selection(config, blueprints_metadata, args)
            logger.debug(f"Selected blueprint after setup wizard: '{blueprint}'")

        if blueprint:
            # Verify blueprint requirements
            blueprint_metadata = blueprints_metadata.get(blueprint, {})
            required_servers = blueprint_metadata.get("required_mcp_servers", [])
            logger.debug(f"Blueprint '{blueprint}' requires MCP servers: {required_servers}")
            all_running, missing_servers = are_required_mcp_servers_running(required_servers, config)
            logger.debug(f"Are all required MCP servers running? {all_running}")

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
                logger.debug(f"User chose to configure missing MCP servers: {configure_missing}")
                if configure_missing in ['yes', 'y']:
                    config = await configure_missing_mcp_servers(missing_servers, config, blueprint_metadata)
                    save_configuration(args.config, config)
                else:
                    print(color_text("Cannot proceed without configuring the required MCP servers.", "red"))
                    logger.warning("User declined to configure missing MCP servers")
                    blueprint = None

        # Run CLI mode with or without blueprint
        try:
            logger.debug("Building agent for CLI mode")
            agent = await build_agent_with_mcp_tools(config)
            logger.info("Agent built successfully for CLI mode")
            await run_cli_mode(agent, colorama_available=True)
        except Exception as e:
            logger.error(f"Fatal error: {e}")
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
        logger.debug("Starting asyncio event loop")
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nReceived shutdown signal (Ctrl+C)")
        logger.info("Received shutdown signal (Ctrl+C)")
        handle_shutdown()
    except Exception as e:
        logger.error(f"Unhandled exception: {e}")
        print(color_text(f"\nFatal error: {e}", "red"))
        handle_shutdown()
        sys.exit(1)
    finally:
        logger.info("Application terminated")
        sys.exit(0)
