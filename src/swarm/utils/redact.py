"""
Utility for redacting sensitive data from logs or outputs.

This module provides a function to redact sensitive keys in dictionaries or lists
for logging purposes, with support for partial reveals.
"""

from typing import Any, List

def redact_sensitive_data(data: Any, sensitive_keys: List[str] = None, mask: str = "****", reveal_chars: int = 4) -> Any:
    """
    Redacts sensitive keys in a dictionary or list for logging purposes, with partial reveal.

    Args:
        data (Any): The data to process (dictionary, list, or other types).
        sensitive_keys (List[str]): List of keys to redact. Defaults to common keys like 'api_key'.
        mask (str): Mask to replace the middle part with.
        reveal_chars (int): Number of characters to reveal at the start and end of sensitive values.

    Returns:
        Any: Data with sensitive keys redacted with partial reveal.
    """
    if sensitive_keys is None:
        sensitive_keys = ["api_key", "OPENAI_API_KEY", "XAI_API_KEY", "BRAVE_API_KEY"]

    def partially_redact(value: str) -> str:
        """Helper function to partially redact sensitive strings."""
        if len(value) <= reveal_chars * 2:
            return mask
        return f"{value[:reveal_chars]}{mask}{value[-reveal_chars:]}"

    if isinstance(data, dict):
        return {
            key: (partially_redact(value) if key in sensitive_keys and isinstance(value, str)
                  else redact_sensitive_data(value, sensitive_keys, mask, reveal_chars))
            for key, value in data.items()
        }
    elif isinstance(data, list):
        return [redact_sensitive_data(item, sensitive_keys, mask, reveal_chars) for item in data]
    elif isinstance(data, str) and any(key in data for key in sensitive_keys):
        return partially_redact(data)
    return data


# Alias for compatibility with older code
redact_sensitive_values = redact_sensitive_data
