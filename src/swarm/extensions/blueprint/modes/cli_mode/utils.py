# src/swarm/extensions/blueprint/modes/cli_mode/utils.py

import logging
from typing import Dict, Optional
from swarm.utils.color_utils import color_text

logger = logging.getLogger(__name__)

def display_message(message: str, message_type: str = "info") -> None:
    """
    Display a message to the user with optional color formatting.

    Args:
        message (str): The message to display.
        message_type (str): The type of message (info, warning, error).
    """
    color_map = {
        "info": "cyan",
        "warning": "yellow",
        "error": "red"
    }
    color = color_map.get(message_type, "cyan")
    print(color_text(message, color))
    if message_type == "error":
        logger.error(message)
    elif message_type == "warning":
        logger.warning(message)
    else:
        logger.info(message)

def prompt_user(prompt: str, default: Optional[str] = None) -> str:
    """
    Prompt the user for input with an optional default value.

    Args:
        prompt (str): The prompt to display to the user.
        default (Optional[str]): The default value to use if the user provides no input.

    Returns:
        str: The user's input or the default value.
    """
    if default:
        prompt = f"{prompt} [{default}]: "
    else:
        prompt = f"{prompt}: "
    user_input = input(prompt).strip()
    return user_input or default

def validate_input(user_input: str, valid_options: list, default: Optional[str] = None) -> str:
    """
    Validate the user's input against a list of valid options.

    Args:
        user_input (str): The user's input.
        valid_options (list): A list of valid options.
        default (Optional[str]): A default value to use if the input is invalid.

    Returns:
        str: The valid input or the default value.
    """
    if user_input in valid_options:
        return user_input
    elif default is not None:
        display_message(f"Invalid input. Using default: {default}", "warning")
        return default
    else:
        display_message(f"Invalid input. Valid options are: {', '.join(valid_options)}", "error")
        raise ValueError(f"Invalid input: {user_input}")

def log_and_exit(message: str, code: int = 1) -> None:
    """
    Log an error message and exit the application.

    Args:
        message (str): The error message to log.
        code (int): The exit code to use.
    """
    logger.error(message)
    display_message(message, "error")
    exit(code)
