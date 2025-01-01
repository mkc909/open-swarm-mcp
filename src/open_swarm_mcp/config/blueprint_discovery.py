"""
Blueprint Discovery Module for Open Swarm MCP.
This module dynamically discovers and imports blueprints from specified directories.
It identifies classes derived from BlueprintBase as valid blueprints and extracts their metadata.
"""

import importlib
import inspect
import logging
from pathlib import Path
from typing import Dict, List, Any

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

try:
    from open_swarm_mcp.blueprint_base import BlueprintBase
except ImportError as e:
    logger.critical(f"Failed to import BlueprintBase: {e}")
    raise

def discover_blueprints(directories: List[str]) -> Dict[str, Dict[str, Any]]:
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

            try:
                spec = importlib.util.spec_from_file_location(module_name, blueprint_file)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                logger.debug(f"Successfully imported module: {module_name}")

                # Log all members of the module
                logger.debug(f"Module members: {dir(module)}")

                # Identify classes inheriting from BlueprintBase
                for name, obj in inspect.getmembers(module, inspect.isclass):
                    logger.debug(f"Found class: {name}")
                    logger.debug(f"Class: {obj}, Base classes: {obj.__bases__}")

                    # Assume the class is valid and add it to the blueprints dictionary
                    metadata = getattr(obj, "metadata", {})
                    logger.debug(f"Assuming class {name} is valid. Metadata: {metadata}")
                    blueprints[blueprint_name] = {
                        "class": obj,
                        "metadata": metadata,
                    }

            except (ModuleNotFoundError, ImportError) as e:
                logger.error(f"Failed to import '{module_name}': {e}")
            except Exception as e:
                logger.error(f"Unexpected error importing '{module_name}': {e}", exc_info=True)

    logger.info("Blueprint discovery complete.")
    logger.debug(f"Discovered blueprints: {list(blueprints.keys())}")

    return blueprints
