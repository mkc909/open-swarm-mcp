import os
import logging
import jmespath
from swarm.utils.logger_setup import setup_logger

# Initialize logger for this module
logger = setup_logger(__name__)


def find_project_root(current_path: str, marker: str = ".git") -> str:
    """
    Recursively search for the project root by looking for a specific marker file or directory.

    Args:
        current_path (str): Starting path for the search.
        marker (str): Marker file or directory to identify the project root.

    Returns:
        str: Path to the project root.

    Raises:
        FileNotFoundError: If the project root cannot be found.
    """
    while True:
        if os.path.exists(os.path.join(current_path, marker)):
            return current_path
        new_path = os.path.dirname(current_path)
        if new_path == current_path:
            break
        current_path = new_path
    raise FileNotFoundError(f"Project root with marker '{marker}' not found.")


def color_text(text: str, color: str = "white") -> str:
    """
    Returns colored text using ANSI escape codes.

    Args:
        text (str): Text to color.
        color (str): Color name. Supported colors: red, green, yellow, blue, magenta, cyan, white.

    Returns:
        str: Colored text string.
    """
    colors = {
        "red": "\033[91m",
        "green": "\033[92m",
        "yellow": "\033[93m",
        "blue": "\033[94m",
        "magenta": "\033[95m",
        "cyan": "\033[96m",
        "white": "\033[97m",
    }
    reset = "\033[0m"
    color_code = colors.get(color.lower(), colors["white"])
    return f"{color_code}{text}{reset}"


def extract_chat_id(payload: dict) -> str:
    """
    Extracts the most recent tool call ID from an assistant message using JMESPath.
    Falls back to the most recent tool call ID if filtering fails.
    """
    # TODO use envvar
    primary_path = "messages[?role=='assistant'].tool_calls[*].id | [-1][-1]"  # Preferred
    alt_path = "reverse(messages)[?role=='assistant'] | [0].tool_calls[-1].id"  # Alternative
    fallback_path = "messages[*].tool_calls[*].id | [-1][-1]"  # Final fallback

    try:
        logger.debug(f"Extracting chat ID with primary JMESPath: {primary_path}")
        chat_id = jmespath.search(primary_path, payload)

        if not chat_id:
            logger.debug(f"Primary failed, trying alternative JMESPath: {alt_path}")
            chat_id = jmespath.search(alt_path, payload)

        if not chat_id:
            logger.debug(f"Alternative failed, trying fallback JMESPath: {fallback_path}")
            chat_id = jmespath.search(fallback_path, payload)

        logger.debug(f"Extracted chat ID: {chat_id}" if chat_id else "No conversation ID found.")
        return chat_id if chat_id else None
    except Exception as e:
        logger.error(f"Error extracting chat ID with JMESPath: {e}", exc_info=True)
        return None
