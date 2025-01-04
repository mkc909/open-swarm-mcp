# swarm/extensions/blueprint/blueprint_base.py

import asyncio  # Add asyncio for asynchronous operations
import logging
import json
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, List

from swarm import Swarm  # Ensure correct import path
from swarm.types import Agent
from swarm.repl import run_demo_loop  # Import run_demo_loop from repl.py

# Configure logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

if not logger.handlers:
    stream_handler = logging.StreamHandler()
    formatter = logging.Formatter("[%(levelname)s] %(asctime)s - %(name)s - %(message)s")
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)


class BlueprintBase(ABC):
    """
    Base class for all blueprint implementations.
    Handles environment variable loading, configuration, agent creation,
    and interactive mode with dynamic tool discovery.
    """

    def __init__(self, config_path: Optional[str] = None, **kwargs):
        """
        Initialize the BlueprintBase with a configuration file path and optional overrides.

        Args:
            config_path (Optional[str]): Path to config file or directory.
            **kwargs: Additional params for future extensibility.
        """
        logger.debug(f"Initializing BlueprintBase with config_path='{config_path}', kwargs={kwargs}")

        # Validate metadata
        if not hasattr(self, 'metadata') or not isinstance(self.metadata, dict):
            raise AssertionError("Blueprint metadata must be defined and must be a dictionary.")

        # Load environment variables from .env
        from dotenv import load_dotenv
        load_dotenv()
        logger.debug("Environment variables loaded from .env.")

        # Initialize Swarm
        self.swarm = Swarm(config_path=config_path)
        logger.info("Swarm instance created.")

        self.starting_agent = None  # Initialize starting agent as None

        # Create and register agents
        agents = self.create_agents()
        self.swarm.agents.update(agents)
        logger.info(f"Agents registered: {list(agents.keys())}")

        # Discover tools for all agents
        asyncio.run(self.async_discover_agent_tools())
        logger.info("Tool discovery completed.")

    def set_starting_agent(self, agent: Agent) -> None:
        """
        Set the starting agent for the blueprint.

        Args:
            agent (Agent): The agent to set as the starting agent.
        """
        logger.debug(f"Setting starting agent to: {agent.name}")
        self.starting_agent = agent

    # --------------------------
    # Abstract / Overridable
    # --------------------------

    @property
    @abstractmethod
    def metadata(self) -> Dict[str, Any]:
        """
        Must be overridden to provide metadata like title, description,
        required MCP servers, and environment variables.
        """
        pass

    @abstractmethod
    def create_agents(self) -> Dict[str, Agent]:
        """
        Must be overridden by child classes to define and create agents.

        Returns:
            Dict[str, Agent]: Dictionary of agents to be registered in Swarm.
        """
        pass

    # --------------------------
    # Agent Tool Discovery
    # --------------------------

    async def async_discover_agent_tools(self, debug: bool = False) -> None:
        """
        Asynchronously discover tools for all agents and merge them into their definitions.

        Args:
            debug (bool): Whether to enable debug logging.
        """
        logger.info("Discovering tools for agents...")
        for agent_name, agent in self.swarm.agents.items():
            logger.debug(f"Discovering tools for agent: {agent_name}")
            try:
                discovered_tools = await self.swarm.discover_and_merge_agent_tools(agent, debug=debug)
                logger.debug(f"Discovered tools for agent '{agent_name}': {discovered_tools}")
            except Exception as e:
                logger.error(f"Failed to discover tools for agent '{agent_name}': {e}")

    # --------------------------
    # Interactive Mode (REPL)
    # --------------------------

    def interactive_mode(self, stream: bool = False) -> None:
        """
        Blocking interactive usage with REPL loop using run_demo_loop.

        Args:
            stream (bool): Whether to enable streaming mode.
        """
        logger.info("Starting interactive_mode.")
        if not self.starting_agent:
            logger.error("Starting agent is not set. Ensure `set_starting_agent` is called.")
            raise ValueError("Starting agent is not set.")
        try:
            run_demo_loop(
                starting_agent=self.starting_agent,
                context_variables={},  # Add context variables if needed
                stream=stream,
                debug=False,
            )
        except Exception as e:
            logger.error(f"Interactive mode failed: {e}")

    # --------------------------
    # Main Entry Point
    # --------------------------

    @classmethod
    def main(cls, stream: bool = False):
        """
        For direct usage: python <blueprint>.py

        Args:
            stream (bool): Whether to enable streaming mode.
        """
        logger.info(f"Running blueprint '{cls.__name__}' as script.")
        blueprint = cls()
        blueprint.interactive_mode(stream=stream)
