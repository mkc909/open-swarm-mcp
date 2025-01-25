"""
Utility for redacting sensitive data from logs or outputs.

This module provides a function to redact sensitive keys in dictionaries or lists
for logging purposes, with support for partial reveals.
"""

import os
from typing import Any, List

def redact_sensitive_data(data: Any, sensitive_keys: List[str] = None, mask: str = "****", reveal_chars: int = 4) -> Any:
    """
    Redacts sensitive keys in a dictionary or list for logging purposes, with partial reveal.

    Args:
        data (Any): The data to process (dictionary, list, or other types).
        sensitive_keys (List[str]): List of keys to redact. Defaults to case-insensitive "api_key" and "token".
        mask (str): Mask to replace the middle part with.
        reveal_chars (int): Number of characters to reveal at the start and end of sensitive values.

    Returns:
        Any: Data with sensitive keys redacted with partial reveal.
    """
    if sensitive_keys is None:
        sensitive_keys = ["api_key", "token"]

    def partially_redact(value: str) -> str:
        """Helper function to partially redact sensitive strings."""
        if len(value) <= reveal_chars * 2:
            return mask
        return f"{value[:reveal_chars]}{mask}{value[-reveal_chars:]}"

    def is_sensitive_key(key: str) -> bool:
        """Helper function to check if a key is sensitive (case-insensitive)."""
        return any(sensitive_key.lower() == key.lower() for sensitive_key in sensitive_keys)

    def is_sensitive_value(value: str) -> bool:
        """Helper function to check if a value matches any environment variable exactly."""
        return value in os.environ.values()

    if isinstance(data, dict):
        return {
            key: (partially_redact(value) if is_sensitive_key(key) and isinstance(value, str) and is_sensitive_value(value)
                  else redact_sensitive_data(value, sensitive_keys, mask, reveal_chars))
            for key, value in data.items()
        }
    elif isinstance(data, list):
        return [redact_sensitive_data(item, sensitive_keys, mask, reveal_chars) for item in data]
    elif isinstance(data, str):
        # Always redact strings if they are sensitive (e.g., API keys)
        return partially_redact(data) if is_sensitive_value(data) else data
    return data