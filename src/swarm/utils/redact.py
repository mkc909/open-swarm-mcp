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

    def is_sensitive_value(value: str, key: str) -> bool:
        """Helper function to check if a value matches the environment variable corresponding to the key."""
        env_var_name = key.upper().replace('_', '')
        return value == os.getenv(env_var_name)

    if isinstance(data, dict):
        new_dict = {}
        for key, value in data.items():
            if isinstance(value, dict) or isinstance(value, list):
                new_dict[key] = redact_sensitive_data(value, sensitive_keys, mask, reveal_chars)
            elif isinstance(value, str):
                if is_sensitive_key(key):
                    new_dict[key] = partially_redact(value)
                else:
                    new_dict[key] = value
            else:
                new_dict[key] = value
        return new_dict
    elif isinstance(data, list):
        return [redact_sensitive_data(item, sensitive_keys, mask, reveal_chars) for item in data]
    elif isinstance(data, str):
        for env_var_name, env_var_value in os.environ.items():
            if data == env_var_value:
                return partially_redact(data)
        return data
    return data