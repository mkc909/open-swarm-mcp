# src/open_swarm_mcp/blueprint_base.py

"""
Abstract Base Class for Blueprints

Defines the structure and required methods for all blueprint implementations.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from swarm import Swarm, Agent

class BlueprintBase(ABC):
    """
    Abstract Base Class for all Blueprints.
    """

    def __init__(self):
        """
        Initialize the blueprint.
        """
        self._metadata: Dict[str, Any] = {}
        self.client = Swarm()
        self.agent: Agent = self.create_agent()

    @property
    @abstractmethod
    def metadata(self) -> Dict[str, Any]:
        """
        Metadata about the blueprint.

        Returns:
            Dict[str, Any]: Metadata dictionary containing title, description, etc.
        """
        pass

    @abstractmethod
    def validate_env_vars(self) -> None:
        """
        Validate that required environment variables are set and any necessary conditions are met.
        """
        pass

    @abstractmethod
    def create_agent(self) -> Agent:
        """
        Create and configure the agent specific to the blueprint.

        Returns:
            Agent: An instance of the Agent configured for the blueprint.
        """
        pass

    @abstractmethod
    def execute(self, config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute the blueprint in framework integration mode.

        Args:
            config (Optional[Dict[str, Any]]): Configuration dictionary from the framework.

        Returns:
            Dict[str, Any]: Execution results containing status, messages, and metadata.
        """
        pass

    def interactive_mode(self) -> None:
        """
        Run the blueprint in standalone interactive mode.
        """
        self.validate_env_vars()
        print(f"Entering {self.metadata.get('title', 'Interactive')} Interactive Mode.")
        print("Type 'exit' to quit.\n")

        messages: list = []

        try:
            while True:
                user_input = input("> ")
                if user_input.lower() == 'exit':
                    print(f"Exiting {self.metadata.get('title', 'Interactive')} Interactive Mode.")
                    break

                messages.append({"role": "user", "content": user_input})
                response = self.client.run(agent=self.agent, messages=messages)
                messages = response.messages  # Update messages with assistant's reply

                # Print the assistant's latest message
                assistant_message = response.messages[-1].get("content", "")
                print(f"assistant: {assistant_message}\n")
        except KeyboardInterrupt:
            print(f"\nInterrupted. Exiting {self.metadata.get('title', 'Interactive')} Interactive Mode.")
        except Exception as e:
            print(f"Error during interactive mode: {e}")
