# src/open_swarm_mcp/blueprint_base.py

"""
Abstract Base Class for Blueprints

Defines the structure and required methods for all blueprint implementations.
"""

import logging
import random
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

from swarm.repl import run_demo_loop
from swarm import Agent

logger = logging.getLogger(__name__)


class BlueprintBase(ABC):
    """
    Abstract Base Class for all Blueprints.
    """

    @abstractmethod
    def __init__(self) -> None:
        """
        Initialize the blueprint.
        """
        ...

    @abstractmethod
    def validate_env_vars(self) -> None:
        """
        Validate that required environment variables are set and any necessary conditions are met.
        """
        ...

    @abstractmethod
    def execute(self, config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute the blueprint in framework integration mode.

        Args:
            config (Optional[Dict[str, Any]]): Configuration dictionary from the framework.

        Returns:
            Dict[str, Any]: Execution results containing status, messages, and metadata.
        """
        ...

    @property
    @abstractmethod
    def metadata(self) -> Dict[str, Any]:
        """
        Metadata about the blueprint.

        Returns:
            Dict[str, Any]: Metadata dictionary containing title, description, etc.
        """
        ...

    @abstractmethod
    def get_agents(self) -> Dict[str, Agent]:
        """
        Return the dictionary of agents used by this blueprint.
        """
        ...

    def get_starting_agent(self) -> Agent:
        """
        By default, pick a random agent from self.get_agents().
        Child classes can override if they want a specific logic.
        """
        agent_map = self.get_agents()
        if not agent_map:
            raise ValueError("No agents defined in this blueprint.")
        return random.choice(list(agent_map.values()))

    def interactive_mode(self) -> None:
        """
        Default interactive mode that uses swarm.repl.run_demo_loop
        with the 'starting_agent' determined by get_starting_agent().
        """
        logger.info("Starting blueprint in interactive mode.")
        starting_agent = self.get_starting_agent()
        logger.info(f"Starting agent: {starting_agent.name}")
        run_demo_loop(starting_agent=starting_agent)
