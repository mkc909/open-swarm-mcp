# src/swarm/utils/general_utils.py

import os
import logging

logger = logging.getLogger(__name__)

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
