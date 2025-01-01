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
    from swarm.blueprint_base import BlueprintBase
except ImportError as e:
    logger.critical(f"Failed to import BlueprintBase: {e}")
    raise


def discover_blueprints(directories: List[str]) -> Dict[str, Dict[str, Any]]:
    """
    Discover and load blueprints from specified directories.
    Extract metadata including title, description, and other attributes.

    Args:
        directories (List[str]): List of directories to search for blueprints.

    Returns:
        Dict[str, Dict[str, Any]]: Dictionary containing blueprint metadata.
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

            try:
                # Dynamically import the blueprint module
                spec = importlib.util.spec_from_file_location(module_name, blueprint_file)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                logger.debug(f"Successfully imported module: {module_name}")

                # Identify classes inheriting from BlueprintBase
                for name, obj in inspect.getmembers(module, inspect.isclass):
                    if issubclass(obj, BlueprintBase) and obj is not BlueprintBase:
                        logger.debug(f"Discovered blueprint class: {name}")

                        # Retrieve metadata
                        try:
                            metadata = obj.metadata
                            # Access the property if callable
                            if isinstance(metadata, property):
                                metadata = metadata.fget(obj)
                            elif callable(metadata):
                                metadata = metadata()

                            if not isinstance(metadata, dict):
                                raise TypeError(f"Expected metadata to be a dictionary, got {type(metadata)} instead.")

                        except Exception as e:
                            logger.error(f"Error retrieving metadata for blueprint '{blueprint_name}': {e}")
                            raise ValueError(f"Metadata for blueprint '{blueprint_name}' is invalid or inaccessible.")

                        # Ensure required metadata fields are present
                        metadata.setdefault("title", blueprint_name.capitalize())
                        metadata.setdefault("description", f"Blueprint for {blueprint_name}")

                        blueprints[blueprint_name] = {
                            "blueprint_class": obj,
                            "title": metadata["title"],
                            "description": metadata["description"],
                        }
                        logger.debug(f"Added blueprint '{blueprint_name}' with metadata: {metadata}")
            except ImportError as e:
                logger.error(f"Failed to import module '{module_name}': {e}")
            except Exception as e:
                logger.error(f"Unexpected error importing '{module_name}': {e}", exc_info=True)

    logger.info("Blueprint discovery complete.")
    logger.debug(f"Discovered blueprints: {list(blueprints.keys())}")
    return blueprints
