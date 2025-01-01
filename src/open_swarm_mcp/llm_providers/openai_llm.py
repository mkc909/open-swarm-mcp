# src/open_swarm_mcp/llm_providers/openai_llm.py

"""
OpenAI LLM Provider Module for Open Swarm MCP.

Defines the OpenAILLMProvider class, which interfaces with OpenAI's API to generate responses.
"""

import logging
from typing import Any, Dict

import aiohttp
import asyncio
import json
import requests

from open_swarm_mcp.llm_providers.base_llm_provider import BaseLLMProvider


logger = logging.getLogger(__name__)


class OpenAILLMProvider(BaseLLMProvider):
    """
    LLM Provider implementation for OpenAI.
    """

    def __init__(
        self,
        model: str,
        api_key: str,
        base_url: str = "https://api.openai.com/v1",
        temperature: float = 0.7,
        max_tokens: int = 150,
    ):
        """
        Initialize the OpenAI LLM Provider with necessary credentials and configurations.

        Args:
            model (str): The model name to use (e.g., 'gpt-4').
            api_key (str): The API key for authentication.
            base_url (str, optional): The base URL for the OpenAI API. Defaults to "https://api.openai.com/v1".
            temperature (float, optional): Sampling temperature. Defaults to 0.7.
            max_tokens (int, optional): Maximum number of tokens in the response. Defaults to 150.
        """
        super().__init__()
        self.model = model
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }
        logger.debug(
            f"Initialized OpenAILLMProvider with model={self.model}, base_url={self.base_url}, "
            f"temperature={self.temperature}, max_tokens={self.max_tokens}"
        )

    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the OpenAI model.

        Returns:
            Dict[str, Any]: Model information.
        """
        info = {
            "model": self.model,
            "provider": "openai",
            "base_url": self.base_url,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }
        logger.debug(f"Model info: {info}")
        return info

    def generate_response(self, prompt: str) -> str:
        """
        Generate a synchronous response from OpenAI based on the provided prompt.

        Args:
            prompt (str): The input prompt for the LLM.

        Returns:
            str: The generated response from the LLM.

        Raises:
            Exception: If the API request fails or returns an error.
        """
        logger.debug(f"Generating response for prompt: {prompt}")
        endpoint = f"{self.base_url}/chat/completions"
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }

        try:
            response = requests.post(endpoint, headers=self.headers, json=payload, timeout=30)
            response.raise_for_status()
            data = response.json()
            logger.debug(f"API response data: {data}")
            choices = data.get("choices", [])
            if not choices:
                error_msg = "No choices returned from OpenAI API."
                logger.error(error_msg)
                raise Exception(error_msg)
            assistant_message = choices[0].get("message", {}).get("content", "")
            logger.debug(f"Assistant response: {assistant_message}")
            return assistant_message.strip()
        except requests.exceptions.RequestException as e:
            logger.error(f"Request to OpenAI API failed: {e}")
            raise Exception(f"OpenAI API request failed: {e}")
        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode JSON response: {e}")
            raise Exception(f"Invalid JSON response from OpenAI API: {e}")

    async def generate_response_async(self, prompt: str) -> str:
        """
        Generate an asynchronous response from OpenAI based on the provided prompt.

        Args:
            prompt (str): The input prompt for the LLM.

        Returns:
            str: The generated response from the LLM.

        Raises:
            Exception: If the API request fails or returns an error.
        """
        logger.debug(f"Generating async response for prompt: {prompt}")
        endpoint = f"{self.base_url}/chat/completions"
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }

        try:
            async with aiohttp.ClientSession(headers=self.headers) as session:
                async with session.post(endpoint, json=payload, timeout=30) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"OpenAI API returned status {response.status}: {error_text}")
                        raise Exception(f"OpenAI API error {response.status}: {error_text}")
                    data = await response.json()
                    logger.debug(f"API response data: {data}")
                    choices = data.get("choices", [])
                    if not choices:
                        error_msg = "No choices returned from OpenAI API."
                        logger.error(error_msg)
                        raise Exception(error_msg)
                    assistant_message = choices[0].get("message", {}).get("content", "")
                    logger.debug(f"Assistant async response: {assistant_message}")
                    return assistant_message.strip()
        except asyncio.TimeoutError:
            logger.error("Async request to OpenAI API timed out.")
            raise Exception("Async request to OpenAI API timed out.")
        except aiohttp.ClientError as e:
            logger.error(f"Async request to OpenAI API failed: {e}")
            raise Exception(f"Async OpenAI API request failed: {e}")
        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode JSON response: {e}")
            raise Exception(f"Invalid JSON response from OpenAI API: {e}")
