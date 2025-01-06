import asyncio
import logging
import sys
import os
import json

from swarm.extensions.blueprint.modes.cli_mode.cli_args import parse_arguments
from swarm.extensions.config.config_manager import (
    add_llm,
    remove_llm,
    add_mcp_server,
    remove_mcp_server,
    load_config,
    save_config
)
from swarm.extensions.blueprint.blueprint_discovery import discover_blueprints
from swarm.utils.color_utils import color_text, initialize_colorama
from swarm.extensions.config.setup_wizard import run_setup_wizard
from swarm.extensions.config.config_loader import (
    validate_and_select_llm_provider,
    inject_env_vars,
    validate_api_keys,
    load_server_config
)
from swarm.extensions.blueprint.modes.cli_mode.blueprint_runner import run_blueprint_mode
from swarm.utils.general_utils import find_project_root

# Initialize logger for main.py
from swarm.utils.logger_setup import setup_logger
logger = setup_logger(__name__)


async def main():
    """
    Main entry point for the Open Swarm MCP application.
    """
    try:
        initialize_colorama()
        logger.debug("Starting main application")
        args = parse_arguments()
        logger.debug(f"Command-line arguments: {args}")

        # Determine project root and ensure .env is loaded correctly
        try:
            project_root = find_project_root(os.path.dirname(__file__))
            logger.debug(f"Project root determined: '{project_root}'")
        except FileNotFoundError as e:
            logger.critical(e)
            print(color_text(str(e), "red"))
            sys.exit(1)

        # Add the project root to sys.path
        if project_root not in sys.path:
            sys.path.insert(0, project_root)
            logger.debug(f"Added '{project_root}' to sys.path")

        # Load environment variables from the project root
        dotenv_path = os.path.join(project_root, ".env")
        if os.path.exists(dotenv_path):
            load_dotenv(dotenv_path=dotenv_path)
            logger.debug(f"Loaded environment variables from '{dotenv_path}'")
        else:
            logger.warning(f"'.env' file not found at '{dotenv_path}'")
            print(color_text(f"'.env' file not found at '{dotenv_path}'. Some functionalities may not work correctly.", "yellow"))

        # Determine configuration path
        if args.command == "run":
            config_path = args.config if args.config else os.path.join(project_root, "swarm_config.json")
        elif args.command == "config":
            # For config commands, assume the config is at project_root/swarm_config.json
            config_path = os.path.join(project_root, "swarm_config.json")
        else:
            # If no command is provided, default to project_root/swarm_config.json
            config_path = os.path.join(project_root, "swarm_config.json")

        # Handle configuration management commands
        if args.command == "config":
            if not args.config_command:
                print(color_text("No valid configuration command provided. Use --help for more information.", "red"))
                logger.error("No valid configuration command provided.")
                sys.exit(1)

            if args.config_command == "add-llm":
                add_llm(config_path)
            elif args.config_command == "remove-llm":
                remove_llm(config_path, args.llm_name)
            elif args.config_command == "add-server":
                add_mcp_server(config_path)
            elif args.config_command == "remove-server":
                remove_mcp_server(config_path, args.server_name)
            else:
                print(color_text("Unknown configuration command provided.", "red"))
                logger.error("Unknown configuration command provided.")
                sys.exit(1)

        elif args.command == "run":
            # Discover blueprints
            blueprints_metadata = discover_blueprints([os.path.join(project_root, "blueprints")])
            logger.debug(f"Discovered blueprints metadata: {blueprints_metadata}")

            # Handle configuration setup
            if args.setup:
                logger.info("Setup flag detected. Running setup wizard.")
                config = run_setup_wizard(config_path, blueprints_metadata)
            else:
                try:
                    config = load_server_config(config_path)
                    logger.info(f"Configuration file detected at '{config_path}'. Loading configuration.")
                    logger.debug(f"Loaded configuration: {config}")
                except (FileNotFoundError, json.JSONDecodeError) as e:
                    logger.warning(f"Configuration issue ({e}). Launching setup wizard.")
                    config = run_setup_wizard(config_path, blueprints_metadata)
                else:
                    selected_llm = validate_and_select_llm_provider(config)
                    config = inject_env_vars(config)
                    config = validate_api_keys(config, selected_llm)
                    logger.debug(f"Configuration after LLM selection and validation: {config}")

            # Handle LLM API key setup
            llm_profile = os.getenv("LLM", "default")
            llm_config = config.get("llm", {}).get(llm_profile, {})
            llm_provider = llm_config.get("provider", "openai")
            api_key = llm_config.get("api_key", "")
            logger.debug(f"LLM provider: {llm_provider}")
            logger.debug(f"LLM API Key from config: {'set' if api_key else 'not set'}")

            if api_key:
                logger.info(f"LLM API Key loaded from configuration for provider '{llm_provider}'.")
            else:
                print(color_text(
                    f"LLM API Key is missing for provider '{llm_provider}'. Please set the corresponding environment variable.", 
                    "yellow"
                ))
                logger.warning(f"LLM API Key is missing for provider '{llm_provider}'. Please set the corresponding environment variable.")

            # Determine which blueprints to load
            if args.blueprint:
                blueprints_to_load = args.blueprint  # List of blueprints specified via command-line
                logger.debug(f"Blueprints specified via --blueprint: {blueprints_to_load}")
            else:
                blueprints_to_load = list(blueprints_metadata.keys())  # Load all available blueprints
                logger.debug("No --blueprint specified. Loading all available blueprints.")

            # Merge LLM configurations from command-line arguments
            if args.llm or args.llm_model or args.temperature is not None:
                if args.llm:
                    config['llm']['default']['provider'] = args.llm
                    logger.info(f"LLM provider overridden to '{args.llm}' via command-line argument.")
                if args.llm_model:
                    config['llm']['default']['model'] = args.llm_model
                    logger.info(f"LLM model overridden to '{args.llm_model}' via command-line argument.")
                if args.temperature is not None:
                    config['llm']['default']['temperature'] = args.temperature
                    logger.info(f"LLM temperature overridden to '{args.temperature}' via command-line argument.")
                save_config(config_path, config)

            # Run in the specified mode
            if args.mode in ["rest", "mcp-host", "cli"]:
                logger.debug(f"Operating in '{args.mode}' mode")
                await run_blueprint_mode(blueprints_to_load, config, blueprints_metadata, args)
            else:
                logger.error(f"Unsupported mode: {args.mode}")
                print(color_text(f"Unsupported mode: {args.mode}", "red"))
                sys.exit(1)

        else:
            print(color_text("No valid command provided. Use --help for more information.", "red"))
            logger.error("No valid command provided.")
            sys.exit(1)
    finally:
        pass

    def handle_exception(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        logger.critical("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))
        print(color_text("A fatal error occurred. Please check the logs for more details.", "red"))

    # Set the global exception handler
    import sys
    sys.excepthook = handle_exception

    if __name__ == "__main__":
        try:
            asyncio.run(main())
        except KeyboardInterrupt:
            print("\nReceived shutdown signal (Ctrl+C)")
            logger.info("Received shutdown signal (Ctrl+C)")
            sys.exit(0)
        except Exception as e:
            logger.error(f"Unhandled exception: {e}")
            print(color_text(f"\nFatal error: {e}", "red"))
            sys.exit(1)
        finally:
            logger.info("Application terminated")
            sys.exit(0)
