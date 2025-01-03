"""
OpenAI Provider Module for MCP.

Defines the OpenAIProvider class for interfacing with OpenAI's API.
"""

import requests
import logging
from typing import Dict

logger = logging.getLogger(__name__)

class OpenAIProvider:
    """
    OpenAI LLM Provider implementation.
    """

    def __init__(self, config: Dict):
        """
        Initialize OpenAIProvider with configuration.

        Args:
            config (Dict): Configuration dictionary containing API details.
        """
        self.api_key = config["api_key"]
        self.model = config["model"]
        self.base_url = config.get("base_url", "https://api.openai.com/v1")
        self.temperature = config.get("temperature", 0.7)
        logger.debug(f"Initialized OpenAIProvider with model {self.model}")

    def generate(self, prompt: str) -> str:
        """
        Generate text using the OpenAI API.

        Args:
            prompt (str): The input prompt.

        Returns:
            str: The generated response.
        """
        endpoint = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": self.temperature,
        }

        try:
            response = requests.post(endpoint, headers=headers, json=payload)
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]
        except Exception as e:
            raise RuntimeError(f"Failed to generate response: {e}")
