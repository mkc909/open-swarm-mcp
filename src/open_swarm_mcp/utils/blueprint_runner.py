# src/open_swarm_mcp/utils/blueprint_runner.py

"""
Blueprint Runner Utility

Provides a standardized way to run blueprints standalone or within the framework.
Handles environment variable validation, user inputs, and generating LLM responses.
"""

import importlib.util
import os
import sys
from typing import Optional, Dict, Any

def load_blueprint(blueprint_path: str) -> Any:
    """
    Dynamically load a blueprint module from the given file path.

    Args:
        blueprint_path (str): Path to the blueprint's Python file.

    Returns:
        The loaded blueprint module.

    Raises:
        ImportError: If the module cannot be imported.
    """
    spec = importlib.util.spec_from_file_location("blueprint_module", blueprint_path)
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)  # type: ignore
    except Exception as e:
        raise ImportError(f"Failed to import blueprint at {blueprint_path}: {e}")
    return module

def run_blueprint_framework(blueprint_module: Any) -> None:
    """
    Runs the blueprint in framework integration mode by invoking its execute() function.

    Args:
        blueprint_module: The loaded blueprint module.

    Raises:
        AttributeError: If the blueprint does not have an execute() function.
    """
    if not hasattr(blueprint_module, 'execute'):
        raise AttributeError("The blueprint does not have an execute() function.")

    execute_func = blueprint_module.execute

    # Optionally, load configuration from environment or a config file
    config = {}

    try:
        result = execute_func(config)
        print("Execution Result:")
        print("Status:", result.get("status"))
        print("Messages:")
        for msg in result.get("messages", []):
            print(f"{msg.get('role')}: {msg.get('content')}")
        print("Metadata:", result.get("metadata"))
    except Exception as e:
        print(f"Error executing blueprint: {e}")

def run_blueprint_interactive(blueprint_module: Any) -> None:
    """
    Runs the blueprint in interactive standalone mode by invoking its interactive_mode() function.

    Args:
        blueprint_module: The loaded blueprint module.

    Raises:
        AttributeError: If the blueprint does not have an interactive_mode() function.
    """
    if not hasattr(blueprint_module, 'interactive_mode'):
        raise AttributeError("The blueprint does not have an interactive_mode() function.")

    interactive_func = blueprint_module.interactive_mode

    try:
        interactive_func()
    except Exception as e:
        print(f"Error in interactive mode: {e}")

def main():
    """
    Entry point for the blueprint runner utility.

    Usage:
        python blueprint_runner.py /path/to/blueprint_<name>.py [--interactive]
    """
    import argparse

    parser = argparse.ArgumentParser(description="Blueprint Runner Utility")
    parser.add_argument("blueprint_path", type=str, help="Path to the blueprint's Python file.")
    parser.add_argument("--interactive", action="store_true", help="Run in interactive mode.")

    args = parser.parse_args()

    blueprint_path = args.blueprint_path
    interactive = args.interactive

    if not os.path.isfile(blueprint_path):
        print(f"Blueprint file does not exist at: {blueprint_path}")
        sys.exit(1)

    try:
        blueprint_module = load_blueprint(blueprint_path)
    except ImportError as e:
        print(e)
        sys.exit(1)

    try:
        if interactive:
            run_blueprint_interactive(blueprint_module)
        else:
            run_blueprint_framework(blueprint_module)
    except AttributeError as e:
        print(e)
        sys.exit(1)
    except Exception as e:
        print(f"An error occurred during blueprint execution: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
