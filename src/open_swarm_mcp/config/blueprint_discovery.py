"""
Blueprint Discovery Module for Open Swarm MCP.

This module dynamically discovers and imports blueprints from specified directories.
It identifies classes derived from BlueprintBase as valid blueprints and extracts their metadata.
"""

import os
import sys
import importlib
import logging
from pathlib import Path
from typing import Dict, List, Any, Type

# Logger setup
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)  # Set DEBUG level for detailed output

# BlueprintBase import
try:
    from open_swarm_mcp.blueprint_base import BlueprintBase
except ImportError as e:
    logger.critical(f"Failed to import BlueprintBase: {e}")
    raise


def discover_blueprints(directories: List[str]) -> Dict[str, Dict[str, Any]]:
    """
    Discover and import blueprints from specified directories.

    Args:
        directories (List[str]): A list of directory paths to search for blueprints.

    Returns:
        Dict[str, Dict[str, Any]]: A dictionary mapping blueprint names to their metadata and class.
    """
    blueprints = {}

    logger.info("Starting blueprint discovery.")
    for directory in directories:
        logger.debug(f"Searching for blueprints in: {directory}")
        dir_path = Path(directory)

        if not dir_path.exists() or not dir_path.is_dir():
            logger.warning(f"Invalid directory: {directory}. Skipping...")
            continue

        for blueprint_file in dir_path.rglob("blueprint_*.py"):
            module_name = blueprint_file.stem
            blueprint_name = module_name.replace("blueprint_", "")
            module_path = str(blueprint_file.parent)

            logger.debug(f"Found blueprint file: {blueprint_file}")
            logger.debug(f"Module name: {module_name}, Blueprint name: {blueprint_name}, Module path: {module_path}")

            if module_path not in sys.path:
                sys.path.insert(0, module_path)

            try:
                module = importlib.import_module(module_name)
                logger.debug(f"Successfully imported module: {module_name}")

                # Identify classes inheriting from BlueprintBase
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if isinstance(attr, type) and issubclass(attr, BlueprintBase) and attr is not BlueprintBase:
                        logger.debug(f"Found blueprint class: {attr_name}")
                        metadata = getattr(attr, "metadata", None)
                        if metadata is None or not isinstance(metadata, dict):
                            logger.warning(f"Blueprint '{blueprint_name}' missing valid 'metadata'. Skipping...")
                            continue
                        blueprints[blueprint_name] = {
                            "class": attr,
                            "metadata": metadata,
                        }

            except ModuleNotFoundError as e:
                logger.error(f"ModuleNotFoundError for '{module_name}': {e}")
            except ImportError as e:
                logger.error(f"ImportError for '{module_name}': {e}")
            except Exception as e:
                logger.error(f"Unexpected error importing '{module_name}': {e}", exc_info=True)

            finally:
                # Safely remove module path to prevent conflicts in future imports
                if module_path in sys.path:
                    sys.path.remove(module_path)

    logger.info("Blueprint discovery complete.")
    logger.debug(f"Discovered blueprints: {list(blueprints.keys())}")

    return blueprints
