# src/open_swarm_mcp/config/blueprint_discovery.py

import os
import importlib.util
import logging
from typing import Dict, Any, Type
from open_swarm_mcp.blueprint_base import BlueprintBase

logger = logging.getLogger(__name__)

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
                        
                        # Find classes inheriting from BlueprintBase
                        blueprint_class = None
                        for attr_name in dir(module):
                            attr = getattr(module, attr_name)
                            if isinstance(attr, type) and issubclass(attr, BlueprintBase) and attr is not BlueprintBase:
                                blueprint_class = attr
                                break

                        if blueprint_class is None:
                            logger.warning(f"No BlueprintBase subclass found in {blueprint_module_path}. Skipping blueprint.")
                            continue

                        # Instantiate the blueprint class
                        blueprint_instance = blueprint_class()

                        # Extract metadata from the metadata property
                        metadata = getattr(blueprint_instance, "metadata", None)
                        if isinstance(metadata, dict):
                            blueprints_metadata[blueprint_dir] = metadata
                            logger.info(f"Discovered blueprint '{blueprint_dir}': {metadata}")
                        else:
                            logger.warning(f"metadata property in {blueprint_module_path} is not a dictionary. Skipping blueprint.")
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
