# Command to list available blueprints

import logging
from swarm.extensions.blueprint.blueprint_discovery import discover_blueprints
from pathlib import Path

logger = logging.getLogger(__name__)

def list_blueprints(directories):
    try:
        directories = directories or [str(Path.cwd() / "blueprints")]
        logger.info(f"Discovering blueprints in directories: {directories}")
        blueprints = discover_blueprints(directories)
        if not blueprints:
            print("No blueprints found.")
            return

        print("Discovered Blueprints:")
        for name, metadata in blueprints.items():
            print(f"- {metadata['title']} ({name}): {metadata['description']}")
    except Exception as e:
        logger.error(f"Error listing blueprints: {e}", exc_info=True)
        print("An error occurred while listing blueprints.")
