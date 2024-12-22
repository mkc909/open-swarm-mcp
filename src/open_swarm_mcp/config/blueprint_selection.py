# src/open_swarm_mcp/config/blueprint_selection.py

import logging
from typing import Dict, Any, Optional

from open_swarm_mcp.utils.color_utils import color_text

logger = logging.getLogger(__name__)

def prompt_user_to_select_blueprint(blueprints_metadata: Dict[str, Dict[str, Any]]) -> Optional[str]:
    """
    Prompt the user to select a blueprint from the available blueprints.

    Args:
        blueprints_metadata (Dict[str, Dict[str, Any]]): Metadata of all discovered blueprints.

    Returns:
        Optional[str]: Selected blueprint name or None if no selection is made.
    """
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
