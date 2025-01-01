
# src/open_swarm_mcp/llm_providers/base_llm_provider.py

from abc import ABC, abstractmethod
from typing import Any, Dict


class BaseLLMProvider(ABC):
    """
    Abstract Base Class for LLM Providers.
    Defines the interface that all LLM Providers must implement.
    """

    @abstractmethod
    def get_model_info(self) -> Dict[str, Any]:
        """
        Retrieve information about the LLM model.

        Returns:
            Dict[str, Any]: Model information.
        """
        pass

    @abstractmethod
    def generate_response(self, prompt: str) -> str:
        """
        Generate a response based on the provided prompt.

        Args:
            prompt (str): The input prompt for the LLM.

        Returns:
            str: The generated response from the LLM.
        """
        pass

    @abstractmethod
    async def generate_response_async(self, prompt: str) -> str:
        """
        Asynchronously generate a response based on the provided prompt.

        Args:
            prompt (str): The input prompt for the LLM.

        Returns:
            str: The generated response from the LLM.
        """
        pass
